"""28-second introduction: approved cover followed by two uninterrupted scenes."""
import os,sys,json,hashlib,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import imageio.v2 as imageio
import intro_preview as base
from finish_cover import ROOT,font,WHITE,GOLD
HERE=Path(__file__).resolve().parent;OUT=HERE/'intro_slow'
DEST=ROOT/'output/video/rescue_drone_intro_slow.mp4'
DURATION=28;FPS=30

class Intro(base.Intro):
    def __init__(self,preview=False):
        super().__init__(preview)
    def frame(self,t):
        if t<4:return super().frame(t)
        if t<16:
            idx=min(359,int((t-4)*30))
            if self.preview:idx=min([0,180,359],key=lambda x:abs(x-idx))
            im=Image.open(OUT/'establish'/f'{idx:04d}.jpg').convert('RGB').resize((1920,1080),Image.Resampling.LANCZOS)
            self.evidence.append(dict(video_time=t,kind='opening_recorded_flight',source_frame=idx,simulation_time=50+idx/30))
        else:
            # Continuous recorded search, 30–54 s, at 2x; no FPV inserts.
            im=self.flight(t-3)
            self.evidence[-1]['video_time']=t
        im=Image.alpha_composite(im.convert('RGBA'),self.shade)
        layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
        label='シミュレーション映像' if t<16 else 'シミュレーション・飛行記録（2倍速）'
        d.text((1824-font(23).getlength(label),62),label,font=font(23),fill='#dce1df',anchor='ls',stroke_width=1,stroke_fill='#10191e')
        if t>=25:
            label='ナレーション：OpenAIのAI音声'
            d.text((1824-font(23).getlength(label),1015),label,font=font(23),fill='#dce1df',anchor='ls',stroke_width=1,stroke_fill='#10191e')
        im=Image.alpha_composite(im,layer)
        layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
        def text(s,x,y,n=52,color=WHITE):
            d.text((x,y),s,font=font(n,'bold'),fill=color,anchor='ls')
        if 5.6<=t<15.6:
            text('人が立ち入りにくい建物を、',96,868)
            text('小型ドローンで捜索',96,942)
            opacity=min(float(base.smooth((t-5.6)/.6)),float(base.smooth((15.6-t)/.6)))
        elif 16.4<=t<19.6:
            text('捜索の指示',96,141,26,GOLD)
            text('「青い服の人を探して」',96,215)
            opacity=min(float(base.smooth((t-16.4)/.4)),float(base.smooth((19.6-t)/.4)))
        elif 20<=t:
            text('言葉による指示で捜索を任せ、',96,868)
            text('操縦の負担を減らす',96,942)
            opacity=float(base.smooth((t-20)/.6))
        else:opacity=0
        layer.putalpha(layer.getchannel('A').point(lambda a:round(a*opacity)))
        im=Image.alpha_composite(im,layer).convert('RGB')
        if t<4.4:im=Image.blend(Image.new('RGB',im.size),im,float(base.smooth((t-4)/.4)))
        if t>27.5:im=Image.blend(im,Image.new('RGB',im.size),float(base.smooth((t-27.5)/.5)))
        return im

def audio():
    sys.path.insert(0,str(ROOT))
    import make_rescue_presentation_audio as old
    generated=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'))
    command=json.loads((OUT/'command.json').read_text(encoding='utf8'))
    clips=[]
    for index,(g,start,maximum,file) in enumerate([(generated[0],4.8,10.3,'voice_00.wav'),(command,16.6,3,'command.wav'),(generated[1],20.2,7,'voice_01.wav')]):
        assert g['transcript_matches'] and g['duration_s']<maximum
        assert hashlib.sha256((OUT/file).read_bytes()).hexdigest()==g['sha256']
        clips.append(dict(index=index,start=start,max_s=maximum,file=file,text=g['text'],caption=''))
    (OUT/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
    old.TMP=OUT;old.PLAN=dict(duration_s=DURATION,flights=[],timeline=[dict(start=t) for t in [0,4,16]])
    old.mix()
    review=json.loads((OUT/'audio_review.json').read_text(encoding='utf8'))
    review.update(voice='OpenAI gpt-realtime-2.1-mini / marin',rotor='No rotor audio added',verbatim_transcripts_verified=True,time_stretch_used=False)
    (OUT/'audio_review.json').write_text(json.dumps(review,indent=2),encoding='utf8')

def preview():
    movie=Intro(True);sheet=Image.new('RGB',(1280,3*392),(7,16,22));d=ImageDraw.Draw(sheet)
    for i,t in enumerate([2,6,12,17.5,22,26.5]):
        im=movie.frame(t);im.save(OUT/f'preview_{i:02}.png')
        x=(i%2)*640;y=(i//2)*392
        d.text((x+12,y+4),str(t)+' s',font=font(20,'en'),fill=WHITE)
        sheet.paste(im.resize((640,360),Image.Resampling.LANCZOS),(x,y+32))
    sheet.save(OUT/'preview_sheet.jpg',quality=95)

def render():
    movie=Intro();os.environ['IMAGEIO_FFMPEG_EXE']='ffmpeg'
    assert len(list((OUT/'establish').glob('*.jpg')))==360
    with imageio.get_writer(OUT/'silent.mp4',fps=FPS,codec='h264_nvenc',macro_block_size=1,
        ffmpeg_params=['-cq','18','-preset','p5','-pix_fmt','yuv420p'],ffmpeg_log_level='error') as writer:
        for i in range(DURATION*FPS):
            writer.append_data(np.asarray(movie.frame(i/FPS)))
            if i%150==0:print('SLOW_INTRO_FRAME',i,flush=True)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'soundtrack.wav'),
        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k',
        '-af','loudnorm=I=-16:TP=-2:LRA=7','-movflags','+faststart','-t',str(DURATION),str(DEST)],check=True)
    (OUT/'source_evidence.json').write_text(json.dumps(dict(video=str(DEST),sha256=hashlib.sha256(DEST.read_bytes()).hexdigest(),
        duration_s=DURATION,fps=FPS,observations=movie.evidence,establish_source=str(OUT/'establish_source.json'),
        timeline=[dict(start=0,end=4,role='approved cover, music only'),dict(start=4,end=16,role='definition, one continuous establishing shot'),
                  dict(start=16,end=28,role='command and continuous recorded search, 2x')],
        previous_versions_preserved=True,full_presentation_modified=False),indent=2),encoding='utf8')
    print('SLOW_INTRO_COMPLETE',DEST,flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
