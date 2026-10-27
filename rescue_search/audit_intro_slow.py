"""Verify the delivered encode, source provenance, timing, and narration mix."""
import json,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw
from intro_slow import Intro,OUT,DEST,DURATION,FPS,HERE,font

probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(DEST)],text=True))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'])==(1920,1080)
assert int(v['nb_frames'])==DURATION*FPS and v['avg_frame_rate']=='30/1'
assert abs(float(probe['format']['duration'])-DURATION)<.05
subprocess.run(['ffmpeg','-v','error','-i',str(DEST),'-f','null','-'],check=True)
qa=OUT/'final_qa';qa.mkdir(exist_ok=True)
times=[2,4.5,6,10,14,15.9,16,17.5,20.5,23.5,26,27.4]
movie=Intro();checks=[]
sheet=Image.new('RGB',(1440,4*302),(7,16,22));d=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
    p=qa/f'frame_{i:02}.png'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(DEST),'-frames:v','1',str(p)],check=True)
    got=Image.open(p).convert('RGB');expected=movie.frame(t)
    mae=float(np.abs(np.asarray(got,dtype=float)-np.asarray(expected,dtype=float)).mean())
    assert mae<6,(t,mae)
    checks.append(dict(time_s=t,source_comparison_mae=mae))
    x=(i%3)*480;y=(i//3)*302
    d.text((x+9,y+4),f'{t:.1f} s',font=font(19,'en'),fill='white')
    sheet.paste(got.resize((480,270),Image.Resampling.LANCZOS),(x,y+32))
sheet.save(qa/'contact_sheet.jpg',quality=95)
voices=json.loads((OUT/'voice_manifest.json').read_text(encoding='utf8'))
assert min(c['start'] for c in voices)>=4
assert all(a['start']+a['duration_s']<b['start'] for a,b in zip(voices,voices[1:]))
assert max(c['start']+c['duration_s'] for c in voices)<27.5
assert all(abs(c['duration_s']-c['original_duration_s'])<.001 for c in voices)
source=json.loads((OUT/'establish_source.json').read_text())
assert source['blend_sha256']==hashlib.sha256((HERE/'scenes/clear/scene.blend').read_bytes()).hexdigest()
rows=[json.loads(s) for s in (HERE/'runs/eval03/clear_blue/trace.jsonl').read_text().splitlines()]
assert len(source['frames'])==360
assert len(list((OUT/'establish').glob('*.jpg')))==360
for f in source['frames']:
    r=rows[f['trace_index']]
    assert r['t']==f['simulation_time'] and r['phase']==f['phase']
assert all(b['simulation_time']>a['simulation_time'] for a,b in zip(source['frames'],source['frames'][1:]))
loud=subprocess.run(['ffmpeg','-hide_banner','-i',str(DEST),'-af','loudnorm=I=-16:TP=-2:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,encoding='utf8',errors='replace',check=True)
stats=json.loads(loud.stderr[loud.stderr.rfind('{'):loud.stderr.rfind('}')+1])
assert -18<float(stats['input_i'])<-14 and float(stats['input_tp'])<=-1.0
report=dict(video=str(DEST),sha256=hashlib.sha256(DEST.read_bytes()).hexdigest(),duration_s=DURATION,
    dimensions=[1920,1080],fps=FPS,frames=DURATION*FPS,full_decode=True,title_music_only=True,
    scene_boundaries_s=[0,4,16,28],continuous_scenes_s=[12,12],typography_body_size_px=52,
    sequential_messages=True,voice_overlap=False,voices_cut_off=False,voice_time_stretch=False,loudness=stats,
    source_frame_checks=checks,establish_recorded_poses_verified=True,visual_review_complete=False,
    audio_listening_review=False,full_presentation_modified=False)
(OUT/'final_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
public=dict(report)
public['narration']=voices
public['source_evidence']=str(OUT/'source_evidence.json')
public['edit_description']='Approved 4-second cover with music only, then two continuous 12-second scenes. Opening definition followed by command and recorded search.'
DEST.with_suffix('.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(success=True,frames=DURATION*FPS,duration_s=DURATION,max_sample_mae=max(c['source_comparison_mae'] for c in checks),loudness=stats['input_i'])))
