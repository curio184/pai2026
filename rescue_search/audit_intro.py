"""Decode the preview and compare sampled frames with their recorded sources."""
import json,subprocess,hashlib,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from intro_preview import Intro,OUT,DEST,DURATION,FPS,font
from intro_preview import OUT as ENVIRONMENT_OUT
if '--openai' in sys.argv:
    from intro_openai import IntroOpenAI as Intro,OUT,DEST

probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(DEST)],text=True))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'])==(1920,1080)
assert int(v['nb_frames'])==780 and v['avg_frame_rate']=='30/1'
assert abs(float(probe['format']['duration'])-26)<.05
subprocess.run(['ffmpeg','-v','error','-i',str(DEST),'-f','null','-'],check=True)
qa=OUT/'final_qa';qa.mkdir(exist_ok=True)
times=[2,3.9,4.3,6,8.4,8.6,10,12.5,13.1,14,16.1,16.6,18,20.3,20.5,21.5,23.3,23.5,24,25.4]
movie=Intro();checks=[]
sheet=Image.new('RGB',(1440,5*300),(7,16,22));d=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
    p=qa/f'frame_{i:02}.png'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(DEST),'-frames:v','1',str(p)],check=True)
    got=Image.open(p).convert('RGB');expected=movie.frame(t)
    mae=float(np.abs(np.asarray(got,dtype=float)-np.asarray(expected,dtype=float)).mean())
    assert mae<6,(t,mae)
    checks.append(dict(time_s=t,source_comparison_mae=mae))
    x=(i%4)*360;y=(i//4)*300
    d.text((x+9,y+6),f'{t:.1f} s',font=font(19,'en'),fill='white')
    sheet.paste(got.resize((360,203),Image.Resampling.LANCZOS),(x,y+36))
sheet.save(qa/'contact_sheet.jpg',quality=95)
voices=json.loads((OUT/'voice_manifest.json').read_text(encoding='utf8'))
assert min(c['start'] for c in voices)>=4
assert all(a['start']+a['duration_s']<b['start'] for a,b in zip(voices,voices[1:]))
assert max(c['start']+c['duration_s'] for c in voices)<25.5
loud=subprocess.run(['ffmpeg','-hide_banner','-i',str(DEST),'-af','loudnorm=I=-16:TP=-2:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,encoding='utf8',errors='replace',check=True)
stats=json.loads(loud.stderr[loud.stderr.rfind('{'):loud.stderr.rfind('}')+1])
assert -18<float(stats['input_i'])<-14 and float(stats['input_tp'])<=-1.0
report=dict(video=str(DEST),sha256=hashlib.sha256(DEST.read_bytes()).hexdigest(),duration_s=26,
    dimensions=[1920,1080],fps=30,frames=780,full_decode=True,title_music_only=True,
    sequential_messages=True,voice_overlap=False,voices_cut_off=False,loudness=stats,
    source_frame_checks=checks,scene_frames={n:len(list((ENVIRONMENT_OUT/n).glob('*.jpg'))) for n in ['ceiling','debris']},
    visual_review_complete=False,audio_listening_review=False,full_presentation_modified=False)
assert report['scene_frames']=={'ceiling':135,'debris':135}
(OUT/'final_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(success=True,frames=780,duration_s=26,max_sample_mae=max(c['source_comparison_mae'] for c in checks),loudness=stats['input_i'])))
