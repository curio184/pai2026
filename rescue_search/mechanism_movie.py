"""Approved one-page architecture, exact narration, restrained input/output animation."""
import os,sys,json,math,hashlib,subprocess,wave
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import imageio.v2 as imageio
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);sys.path.insert(0,str(ROOT))
HERE=Path(__file__).resolve().parent;OUT=HERE/'mechanism_movie';OUT.mkdir(exist_ok=True)
SLIDE=ROOT/'output/video/mechanism_review/mechanism_refined.png'
INTRO=ROOT/'output/video/rescue_drone_intro_pan.mp4'
DEST=ROOT/'output/video/rescue_drone_mechanism.mp4'
COMBINED=ROOT/'output/video/rescue_drone_intro_and_mechanism.mp4'
FPS=24;DURATION=28
CYAN=(124,202,198);GOLD=(223,191,138)
STARTS=[1,5.45,13,21.5]
CAPTIONS=[['ドローンの飛行を制御するために、VLAを利用します。'],
 ['VLAは、カメラ映像と言葉による指示から、','次の動作を生成するAIです。'],
 ['ドローンの映像を無線でパソコンへ送り、','VLAが生成した動作を飛行指令として返します。'],
 ['このやり取りを繰り返すことで、','ドローンを自律的に制御します。']]

@lru_cache(None)
def font(n,weight=450):
    f=ImageFont.truetype('C:/Windows/Fonts/NotoSansJP-VF.ttf',n);f.set_variation_by_axes([weight]);return f
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)

def setup():
    import make_rescue_presentation_audio as old
    generated=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'));clips=[]
    for i,(g,start) in enumerate(zip(generated,STARTS)):
        assert g['transcript_matches'] and ''.join(CAPTIONS[i])==g['text']
        assert hashlib.sha256((OUT/g['file']).read_bytes()).hexdigest()==g['sha256']
        clips.append(dict(index=i,start=start,max_s=g['duration_s']+.2,text=g['text'],caption=g['text'],file=g['file']))
    (OUT/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
    old.TMP=OUT;old.PLAN=dict(duration_s=DURATION,flights=[],timeline=[dict(start=0)]);old.mix()
    review=json.loads((OUT/'audio_review.json').read_text());review.update(voice='OpenAI gpt-realtime-2.1-mini / marin',rotor='None',time_stretch_used=False)
    (OUT/'audio_review.json').write_text(json.dumps(review,indent=2))
    with wave.open(str(OUT/'dry_narration.wav'),'wb') as dst:
        dst.setnchannels(1);dst.setsampwidth(2);dst.setframerate(24000)
        for i in range(4):
            with wave.open(str(OUT/f'voice_{i:02}.wav'),'rb') as src:
                assert src.getframerate()==24000;dst.writeframes(src.readframes(src.getnframes()))
            dst.writeframes(bytes(24000))

class Movie:
    def __init__(self):
        self.base=Image.open(SLIDE).convert('RGBA')
        self.voices=json.loads((OUT/'voice_manifest.json').read_text(encoding='utf8'))
        record=HERE/'runs/eval03/clear_blue';score=json.loads((record/'search_score.json').read_text())
        packet=next(p for p in json.loads((record/'vla_link_events.json').read_text()) if p.get('event')=='inference' and p['sim_time_capture']>=score['discovery_time_s'])
        file=record/'observations'/packet['image_file'];assert hashlib.sha256(file.read_bytes()).hexdigest()==packet['image_sha256']
        self.thumb=Image.open(file).convert('RGB').resize((56,42),Image.Resampling.LANCZOS)
        self.packet=packet
    def frame(self,t):
        im=self.base.copy();layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
        def dot(x,y,col,r=5):
            d.ellipse((x-r-4,y-r-4,x+r+4,y+r+4),fill=(*col,35))
            d.ellipse((x-r,y-r,x+r,y+r),fill=(*col,245))
        def pulse(k):
            a=round(155*math.sin(math.pi*max(0,min(1,k))))
            d.line((1375,679,1617,679),fill=(*CYAN,a),width=3)
        def image_input(p):
            p=smooth(p);x=658+(1170-658)*p
            # A real recorded camera image travelling along the existing input lane.
            tile=Image.new('RGBA',(60,46),(*CYAN,220));tile.paste(self.thumb,(2,2));layer.alpha_composite(tile,(round(x-30),490))
        def language_input(p):
            p=smooth(p);dot(1496,309+40*p,CYAN,5)
            d.line((1327,295,1666,295),fill=(*CYAN,round(140*math.sin(math.pi*p))),width=2)
        def internal_input(p):dot(1496,541+41*smooth(p),CYAN)
        def output(p):
            distance=smooth(p)*(61+838)
            x,y=(1496,749+distance) if distance<=61 else (1496-(distance-61),810)
            # Three short bars represent a generated sequence, not measured actuator data.
            for j in range(3):
                d.rounded_rectangle((x-10+j*8,y-8,x-5+j*8,y+8),radius=1,fill=(*GOLD,235-j*30))
        if 1.25<t<4.7:pulse((t-1.25)/3.45)
        elif 5.7<=t<12.4:
            u=t-5.7
            if u<2.7:image_input(u/2.7);language_input(u/2.7)
            elif u<3.5:internal_input((u-2.7)/.8)
            else:pulse((u-3.5)/3.2)
        elif 13.1<=t<21:
            u=t-13.1
            if u<3.2:image_input(u/3.2)
            elif u<3.9:internal_input((u-3.2)/.7);language_input((u-3.2)/.7)
            elif u<5.2:pulse((u-3.9)/1.3)
            else:output((u-5.2)/2.7)
        elif 21.5<=t<27.5:
            u=(t-21.5)%3
            if u<1.1:image_input(u/1.1)
            elif u<1.6:internal_input((u-1.1)/.5);pulse((u-1.1)/.5)
            else:output((u-1.6)/1.4)
        im=Image.alpha_composite(im,layer);d=ImageDraw.Draw(im)
        for i,v in enumerate(self.voices):
            if v['start']<=t<v['start']+v['duration_s']+.12:
                lines=CAPTIONS[i];f=font(36,500)
                for j,s in enumerate(lines):
                    width=f.getlength(s);assert width<1710
                    y=1006 if len(lines)==1 else 979+j*51
                    d.text(((1920-width)/2,y),s,font=f,fill='#eef1ee',anchor='ls')
        im=im.convert('RGB')
        if t<.4:im=Image.blend(Image.new('RGB',im.size),im,smooth(t/.4))
        if t>DURATION-.5:im=Image.blend(im,Image.new('RGB',im.size),smooth((t-(DURATION-.5))/.5))
        return im

def preview():
    movie=Movie();sheet=Image.new('RGB',(1280,3*390),'#091319');d=ImageDraw.Draw(sheet)
    for i,t in enumerate([2.5,7,10,14,19.5,23.5]):
        im=movie.frame(t);im.save(OUT/f'preview_{i:02}.png');x=i%2*640;y=i//2*390
        d.text((x+10,y+2),f'{t:.1f} s',font=font(20),fill='white');sheet.paste(im.resize((640,360)),(x,y+30))
    sheet.save(OUT/'preview_sheet.jpg',quality=95)

def render():
    movie=Movie();os.environ['IMAGEIO_FFMPEG_EXE']='ffmpeg'
    with imageio.get_writer(OUT/'silent.mp4',fps=FPS,codec='h264_nvenc',macro_block_size=1,
        ffmpeg_params=['-cq','18','-preset','p5','-pix_fmt','yuv420p'],ffmpeg_log_level='error') as w:
        for i in range(round(DURATION*FPS)):
            w.append_data(np.asarray(movie.frame(i/FPS)))
            if i%120==0:print('MECHANISM_FRAME',i,flush=True)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0',
      '-c:v','copy','-c:a','aac','-b:a','192k','-ar','96000','-af','loudnorm=I=-16:TP=-2:LRA=7',
      '-movflags','+faststart','-t',str(DURATION),str(DEST)],check=True)
    intro_hash=hashlib.sha256(INTRO.read_bytes()).hexdigest()
    # Stream-copy the accepted intro and new section; never re-render or change the accepted intro.
    listing=OUT/'join.ffconcat'
    listing.write_text('ffconcat version 1.0\n'+''.join("file '"+str(p.resolve()).replace('\\','/')+"'\n" for p in [INTRO,DEST]),encoding='utf8')
    subprocess.run(['ffmpeg','-v','warning','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(COMBINED)],check=True)
    assert hashlib.sha256(INTRO.read_bytes()).hexdigest()==intro_hash
    evidence=dict(section=str(DEST),combined=str(COMBINED),section_duration_s=DURATION,combined_nominal_duration_s=24+DURATION,
       accepted_intro_sha256=intro_hash,slide_sha256=hashlib.sha256(SLIDE.read_bytes()).hexdigest(),
       narration_source=str(OUT/'generation_manifest.json'),camera_input=movie.packet,diagram_unchanged=True,
       animations='Recorded camera thumbnail and language-input highlight; conceptual action-sequence bars follow existing arrows',
       intro_stream_copied=True,no_hardware_validation_claim=True)
    (OUT/'source_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
    print('MECHANISM_COMPLETE',COMBINED,flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
