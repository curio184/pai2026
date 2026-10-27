"""Atmospheric introduction with restored studio background and verbatim subtitles."""
import os,sys,json,hashlib,subprocess,shutil
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import imageio.v2 as imageio
from finish_cover import ROOT,font,WHITE,GOLD,tracked
from intro_preview import smooth
HERE=Path(__file__).resolve().parent;OUT=HERE/'intro_atmosphere';OUT.mkdir(exist_ok=True)
DEST=ROOT/'output/video/rescue_drone_intro_atmosphere.mp4'
DURATION=24;FPS=24
HEADING='災害救助ドローンとは'
CAPTIONS=[(4.8,11.55,['災害救助ドローンとは、人が立ち入りにくい場所で、','被災者の捜索を支援するドローンです。']),
          (15.7,22.05,['今回は、言葉による指示で捜索を任せ、','操縦の負担を減らすことを目指しました。'])]

def foreground():
    im=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(im);x=140
    def put(s,x,y,n,kind='jp',fill=WHITE):d.text((x,y),s,font=font(n,kind),fill=fill,anchor='ls')
    d.rectangle((88,314,94,555),fill=GOLD)
    tracked(d,'PHYSICAL AI',(x,342),font(25,'en'),GOLD,2.2)
    put('災害救助ドローン',x,460,82,'bold')
    put('― VLAによる自律飛行と被災者捜索 ―',x,546,31,fill='#dae1e2')
    d.line((x,625,796,625),fill='#39484e',width=1)
    for i,(name,role) in enumerate([('SmolVLA','（動作生成）'),('ArduPilot','（姿勢制御）'),('StampFly','（ドローン）')]):
        center=240+i*228
        put(name,center-font(33,'en').getlength(name)/2,695,33,'en',GOLD)
        put(role,center-font(25).getlength(role)/2,739,25,fill='#c4cfd2')
        if i<2:put('×',center+114-font(24).getlength('×')/2,720,24,fill='#819097')
    return im

class Intro:
    def __init__(self,preview=False):
        self.preview=preview;self.title=foreground();self.evidence=[]
        y,x=np.mgrid[:1080,:1920]
        self.title_alpha=(.10+.75/(1+np.exp((x-820)/120))+.06*np.clip((y-900)/180,0,1))[...,None]
        alpha=.32*np.clip((190-y)/190,0,1)+.60*np.clip((y-820)/260,0,1)
        overlay=np.zeros((1080,1920,4),np.uint8);overlay[:,:,:3]=[5,12,17];overlay[:,:,3]=(alpha*255).astype('uint8')
        self.shade=Image.fromarray(overlay,'RGBA')
        self.vignette=(1-.12*np.clip(((x-960)/1100)**2+((y-540)/740)**2,0,1))[...,None]
    def frame(self,t):
        if t<4:
            idx=min(239,round(t*30));p=ROOT/'tmp/premium/opening'/f'{idx:04d}.jpg'
            source=Image.open(p).convert('RGB')
            im=Image.new('RGB',(1920,1080),(7,16,22));im.paste(source,(180,0))
            a=np.asarray(im,dtype=np.float32)
            a=a*(1-self.title_alpha)+np.array([7,16,22])*self.title_alpha
            im=Image.alpha_composite(Image.fromarray(np.uint8(np.clip(a,0,255))).convert('RGBA'),self.title).convert('RGB')
            self.evidence.append(dict(video_time=t,kind='studio',source_frame=idx))
            if t>3.65:im=Image.blend(im,Image.new('RGB',im.size),float(smooth((t-3.65)/.35)))
            return im
        name,start,count=('ceiling',4,144) if t<10 else ('rubble',10,144) if t<16 else ('drone',16,192)
        idx=min(count-1,max(0,round((t-start)*24)))
        if self.preview:idx=min([0,count//2,count-1],key=lambda i:abs(i-idx))
        p=OUT/name/f'{idx:04d}.jpg';im=Image.open(p).convert('RGB').resize((1920,1080),Image.Resampling.LANCZOS)
        a=np.asarray(im,dtype=np.float32)/255
        a=((a-.15)*1.1+.13)*np.array([.97,.985,1.01])*self.vignette
        im=Image.fromarray(np.uint8(np.clip(a*255,0,255))).convert('RGBA')
        im=Image.alpha_composite(im,self.shade);d=ImageDraw.Draw(im)
        d.rectangle((65,65,70,103),fill=GOLD)
        d.text((96,100),HEADING,font=font(36,'bold'),fill=WHITE,anchor='ls')
        for begin,end,lines in CAPTIONS:
            if begin<=t<end+.2:
                for j,line in enumerate(lines):
                    f=font(42,'bold');width=f.getlength(line);assert width<1728
                    d.text(((1920-width)/2,930+j*60),line,font=f,fill=WHITE,anchor='ls',stroke_width=1,stroke_fill='#142026')
        self.evidence.append(dict(video_time=t,kind='atmospheric_insert',shot=name,source_frame=idx))
        im=im.convert('RGB')
        if t<4.4:im=Image.blend(Image.new('RGB',im.size),im,float(smooth((t-4)/.4)))
        if t>23.5:im=Image.blend(im,Image.new('RGB',im.size),float(smooth((t-23.5)/.5)))
        return im

def audio():
    sys.path.insert(0,str(ROOT));import make_rescue_presentation_audio as old
    generated=json.loads((HERE/'intro_slow/generation_manifest.json').read_text(encoding='utf8'))
    clips=[]
    for i,(g,start) in enumerate(zip(generated,[4.8,15.7])):
        name=f'voice_{i:02}.wav';shutil.copy2(HERE/'intro_slow'/name,OUT/name)
        assert g['transcript_matches'] and hashlib.sha256((OUT/name).read_bytes()).hexdigest()==g['sha256']
        assert ''.join(CAPTIONS[i][2])==g['text']
        clips.append(dict(index=i,start=start,max_s=7.3,text=g['text'],caption=g['text'],file=name))
    (OUT/'generation_manifest.json').write_text(json.dumps(generated,ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
    old.TMP=OUT;old.PLAN=dict(duration_s=DURATION,flights=[],timeline=[dict(start=0),dict(start=4)])
    old.mix()
    review=json.loads((OUT/'audio_review.json').read_text())
    review.update(voice='OpenAI gpt-realtime-2.1-mini / marin',rotor='No rotor audio added',verbatim_subtitles=True,time_stretch_used=False)
    (OUT/'audio_review.json').write_text(json.dumps(review,indent=2))

def preview():
    movie=Intro(True);sheet=Image.new('RGB',(1280,3*392),(7,16,22));d=ImageDraw.Draw(sheet)
    for i,t in enumerate([2,6,10.5,14,18,22.5]):
        im=movie.frame(t);im.save(OUT/f'preview_{i:02}.png')
        x=i%2*640;y=i//2*392;d.text((x+12,y+5),str(t)+' s',font=font(20,'en'),fill=WHITE)
        sheet.paste(im.resize((640,360),Image.Resampling.LANCZOS),(x,y+32))
    sheet.save(OUT/'preview_sheet.jpg',quality=95)
    movie.frame(2).save(ROOT/'output/video/cover_editorial/cover_studio_background.png')

def render():
    movie=Intro();os.environ['IMAGEIO_FFMPEG_EXE']='ffmpeg'
    assert all(len(list((OUT/n).glob('*.jpg')))==c for n,c in [('ceiling',144),('rubble',144),('drone',192)])
    with imageio.get_writer(OUT/'silent.mp4',fps=FPS,codec='h264_nvenc',macro_block_size=1,
        ffmpeg_params=['-cq','18','-preset','p5','-pix_fmt','yuv420p'],ffmpeg_log_level='error') as writer:
        for i in range(DURATION*FPS):
            writer.append_data(np.asarray(movie.frame(i/FPS)))
            if i%96==0:print('ATMOSPHERE_COMPOSITE',i,flush=True)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'soundtrack.wav'),
        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k',
        '-af','loudnorm=I=-16:TP=-2:LRA=7','-movflags','+faststart','-t',str(DURATION),str(DEST)],check=True)
    (OUT/'source_evidence.json').write_text(json.dumps(dict(video=str(DEST),sha256=hashlib.sha256(DEST.read_bytes()).hexdigest(),
        duration_s=DURATION,fps=FPS,observations=movie.evidence,scene_source=str(OUT/'scene_source.json'),
        title_text_and_coordinates_unchanged=True,title_background='Original studio opening sequence requested by user; shifted 180px right to protect text area',
        heading=HEADING,subtitles=CAPTIONS,on_screen_voice_credit=False,on_screen_simulation_label=False,
        previous_versions_preserved=True,full_presentation_modified=False),ensure_ascii=False,indent=2),encoding='utf8')
    print('ATMOSPHERE_COMPLETE',DEST,flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
