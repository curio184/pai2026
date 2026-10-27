"""OpenAI narration edition of the 26-second preview; retain the prior version."""
import os,json,hashlib,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import imageio.v2 as imageio
import intro_preview as base
from finish_cover import ROOT,font
HERE=Path(__file__).resolve().parent
OUT=HERE/'intro_openai'
DEST=ROOT/'output/video/rescue_drone_intro_openai.mp4'

class IntroOpenAI(base.Intro):
    def __init__(self,preview=False):
        super().__init__(preview,second_message='言葉による指示で捜索を任せ、')
    def frame(self,t):
        im=super().frame(t)
        if 23.4<=t<26:
            layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
            s='ナレーション：OpenAIのAI音声';f=font(23)
            d.text((1824-f.getlength(s),1015),s,font=f,fill='#dce1df',anchor='ls',stroke_width=1,stroke_fill='#10191e')
            opacity=float(base.smooth((26-t)/.5))
            layer.putalpha(layer.getchannel('A').point(lambda a:round(a*opacity)))
            im=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
        return im

def audio():
    import make_rescue_presentation_audio as old
    generated=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'))
    clips=json.loads((base.OUT/'narration_plan.json').read_text(encoding='utf8'))
    for clip,g in zip(clips,generated):
        assert g['transcript_matches'] and g['duration_s']<clip['max_s']
        clip['text']=g['text'];clip['caption']=''
    (OUT/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
    old.TMP=OUT;old.PLAN=dict(duration_s=26,flights=[],timeline=[dict(start=t) for t in [0,4,8.5,13,20.4,23.4]])
    old.mix()
    review=json.loads((OUT/'audio_review.json').read_text(encoding='utf8'))
    review.update(voice='OpenAI '+generated[0]['model']+' / '+generated[0]['voice'],
                  rotor='No rotor audio added',verbatim_transcripts_verified=True,time_stretch_used=False,
                  disclosure='End of preview: narration is OpenAI AI-generated audio')
    (OUT/'audio_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf8')

def render():
    movie=IntroOpenAI();os.environ['IMAGEIO_FFMPEG_EXE']='ffmpeg'
    with imageio.get_writer(OUT/'silent.mp4',fps=30,codec='h264_nvenc',macro_block_size=1,
        ffmpeg_params=['-cq','18','-preset','p5','-pix_fmt','yuv420p'],ffmpeg_log_level='error') as writer:
        for i in range(780):
            writer.append_data(np.asarray(movie.frame(i/30)))
            if i%150==0:print('OPENAI_INTRO_FRAME',i,flush=True)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'soundtrack.wav'),
        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k',
        '-af','loudnorm=I=-16:TP=-2:LRA=7','-movflags','+faststart','-t','26',str(DEST)],check=True)
    (OUT/'source_evidence.json').write_text(json.dumps(dict(video=str(DEST),sha256=hashlib.sha256(DEST.read_bytes()).hexdigest(),
        duration_s=26,fps=30,source_run='eval03/clear_blue',observations=movie.evidence,
        environment_source=str(base.OUT/'environment_source.json'),
        speech_generation=str(OUT/'generation_manifest.json'),original_version_preserved=True),indent=2),encoding='utf8')
    print('OPENAI_INTRO_COMPLETE',DEST,flush=True)

if __name__=='__main__':audio();render()
