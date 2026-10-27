"""26-second editorial preview from approved cover and real search records."""
import os,json,sys,hashlib,subprocess,bisect,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import imageio.v2 as imageio
from finish_cover import ROOT,font,GOLD,WHITE
from edit_movie import Record
HERE=Path(__file__).resolve().parent;OUT=HERE/'intro_preview';OUT.mkdir(exist_ok=True)
DEST=ROOT/'output/video/rescue_drone_intro_preview.mp4'
DURATION=26;FPS=30

def setup():
    clips=[dict(index=0,start=4.6,max_s=7.8,text='人が立ち入りにくい建物を、小型ドローンで捜索します。',caption='',file='voice_00.wav'),
           dict(index=1,start=13.25,max_s=2.9,text='青い服の人を探して。',caption='',file='voice_01.wav'),
           dict(index=2,start=16.5,max_s=8.8,text='言葉の指示で捜索を任せ、操縦の負担を減らすことを目指します。',caption='',file='voice_02.wav')]
    (OUT/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'voice.ps1').write_text((HERE/'movie/voice.ps1').read_text(encoding='utf-8-sig'),encoding='utf-8-sig')
    print('INTRO_PLAN_READY')

def audio():
    import make_rescue_presentation_audio as old
    old.TMP=OUT
    old.PLAN=dict(duration_s=DURATION,flights=[],timeline=[dict(start=t) for t in [0,4,8.5,13,20.4,23.4]])
    old.mix()
    review=json.loads((OUT/'audio_review.json').read_text(encoding='utf8'))
    review['rotor']='No rotor audio added; local narration and original synthesized score only'
    (OUT/'audio_review.json').write_text(json.dumps(review,indent=2),encoding='utf8')

def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)

class Intro:
    def __init__(self,preview=False,second_message='言葉の指示で捜索を任せ、'):
        self.preview=preview
        self.second_message=second_message
        self.cover=Image.open(ROOT/'output/video/cover_editorial/cover_single_line.png').convert('RGB')
        approved=json.loads((ROOT/'output/video/cover_editorial/approved_cover.json').read_text(encoding='utf-8-sig'))
        assert hashlib.sha256((ROOT/'output/video/cover_editorial/cover_single_line.png').read_bytes()).hexdigest()==approved['sha256']
        self.record=Record(HERE/'runs/eval03/clear_blue')
        self.poses=json.loads((HERE/'movie/renders/demo/poses.json').read_text())
        self.evidence=[];self.inputs={}
        yy=np.arange(1080)[:,None]
        alpha=(.08+.77*np.clip((yy-630)/450,0,1))*255
        a=np.zeros((1080,1920,4),dtype=np.uint8);a[:,:,:3]=[5,13,19];a[:,:,3]=np.repeat(alpha.astype('uint8'),1920,axis=1)
        self.shade=Image.fromarray(a,'RGBA')
    def env(self,name,index):
        if self.preview:index=67
        path=OUT/name/f'{index:04d}.jpg'
        deadline=time.monotonic()+900
        while not path.exists() or time.time()-path.stat().st_mtime<.2:
            if time.monotonic()>deadline:raise TimeoutError(str(path))
            time.sleep(.2)
        return Image.open(path).convert('RGB')
    def flight(self,t,fpv=False):
        sim=30+(t-13)*2;idx=min(959,max(0,round((sim-16)*15)))
        if not fpv:
            im=Image.open(HERE/'movie/renders/demo'/f'{idx:04d}.jpg').convert('RGB')
            im=im.crop((0,40,1280,760)).resize((1920,1080),Image.Resampling.LANCZOS)
            self.evidence.append(dict(video_time=t,kind='external',source_frame=idx,**self.poses[idx]))
        else:
            _,r,p,raw=self.record.at(sim)
            assert p is not None
            if p['id'] not in self.inputs:
                self.inputs[p['id']]=raw.resize((1440,1080),Image.Resampling.LANCZOS)
            im=Image.new('RGB',(1920,1080),(7,16,22));im.paste(self.inputs[p['id']],(240,0))
            self.evidence.append(dict(video_time=t,kind='original_input',packet=p['id'],image=p['image_file'],sha256=p['image_sha256'],capture_time=p['sim_time_capture']))
        return im
    def frame(self,t):
        if t<4:
            im=self.cover.copy()
            if t>3.65:im=Image.blend(im,Image.new('RGB',im.size),float(smooth((t-3.65)/.35)))
            return im
        if t<8.5:im=self.env('ceiling',min(134,int((t-4)*30)))
        elif t<13:im=self.env('debris',min(134,int((t-8.5)*30)))
        else:im=self.flight(t,20.4<=t<23.4)
        im=Image.alpha_composite(im.convert('RGBA'),self.shade).convert('RGB')
        layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
        def txt(s,x,y,n=52,color=WHITE,kind='bold'):
            d.text((x,y),s,font=font(n,kind),fill=color,anchor='ls',stroke_width=1 if n<30 else 0,stroke_fill='#10191e')
        label='シミュレーション' if t<13 else 'シミュレーション・飛行記録（2倍速）'
        txt(label,1824-font(23).getlength(label),62,23,'#dce1df','jp')
        if 20.4<=t<23.4:txt('VLAに入力した画像',96,62,23,'#dce1df','jp')
        im=Image.alpha_composite(im.convert('RGBA'),layer)
        layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
        if 4.5<=t<12.75:
            txt('人が立ち入りにくい建物を、',96,868)
            txt('小型ドローンで捜索',96,942)
            opacity=min(float(smooth((t-4.5)/.45)),float(smooth((12.75-t)/.35)))
        elif 13.15<=t<16.3:
            txt('捜索の指示',96,141,26,GOLD)
            txt('「青い服の人を探して」',96,215,52)
            opacity=min(float(smooth((t-13.15)/.3)),float(smooth((16.3-t)/.3)))
        elif 16.4<=t<26:
            txt(self.second_message,96,868)
            txt('操縦の負担を減らす',96,942)
            opacity=float(smooth((t-16.4)/.4))
        else:opacity=0
        layer.putalpha(layer.getchannel('A').point(lambda a:round(a*opacity)))
        im=Image.alpha_composite(im,layer).convert('RGB')
        if t<4.35:im=Image.blend(Image.new('RGB',im.size),im,float(smooth((t-4)/.35)))
        if t>25.5:im=Image.blend(im,Image.new('RGB',im.size),float(smooth((t-25.5)/.5)))
        return im

def preview():
    movie=Intro(True);times=[2,6,10,14,18,21.5,24]
    sheet=Image.new('RGB',(960,7*300),(7,16,22));d=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        im=movie.frame(t);im.save(OUT/f'preview_{i:02}.png')
        sheet.paste(im.resize((480,270),Image.Resampling.LANCZOS),(0,i*300+30))
        d.text((15,i*300+4),str(t)+' s',font=font(20,'en'),fill=WHITE)
    # Two columns, four rows for an economical review sheet.
    sheet=Image.new('RGB',(960,4*302),(7,16,22));d=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        x=(i%2)*480;y=(i//2)*302
        d.text((x+12,y+4),str(t)+' s',font=font(20,'en'),fill=WHITE)
        im=Image.open(OUT/f'preview_{i:02}.png').resize((480,270),Image.Resampling.LANCZOS)
        sheet.paste(im,(x,y+32))
    sheet.save(OUT/'preview_sheet.jpg',quality=95)

def render():
    movie=Intro();os.environ['IMAGEIO_FFMPEG_EXE']='ffmpeg'
    silent=OUT/'silent.mp4'
    with imageio.get_writer(silent,fps=30,codec='h264_nvenc',macro_block_size=1,
            ffmpeg_params=['-cq','18','-preset','p5','-pix_fmt','yuv420p'],ffmpeg_log_level='error') as writer:
        for i in range(DURATION*FPS):
            writer.append_data(np.asarray(movie.frame(i/FPS)))
            if i%150==0:print('INTRO_COMPOSITE',i,flush=True)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(silent),'-i',str(OUT/'soundtrack.wav'),
        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k',
        '-af','loudnorm=I=-16:TP=-2:LRA=7','-movflags','+faststart','-t',str(DURATION),str(DEST)],check=True)
    (OUT/'source_evidence.json').write_text(json.dumps(dict(duration_s=DURATION,fps=FPS,
        source_run='eval03/clear_blue',flight_record_reused=True,environment_scene_unchanged=True,
        timeline=[dict(start=0,end=4,role='approved title, music only'),dict(start=4,end=13,role='environment establishing shots'),
                  dict(start=13,end=26,role='actual search record; 30–56 simulation seconds at 2x')],
        observations=movie.evidence,video=str(DEST),sha256=hashlib.sha256(DEST.read_bytes()).hexdigest()),indent=2),encoding='utf8')
    print('INTRO_MASTER_COMPLETE',DEST,flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
