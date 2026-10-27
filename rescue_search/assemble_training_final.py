"""Assemble and verify the full film with the approved animated fine-tuning scene."""
import os,json,hashlib,subprocess,concurrent.futures
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
from ending_movie import join
from demo_movie import font
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);HERE=Path(__file__).resolve().parent
OUT=HERE/'final_with_training';OUT.mkdir(exist_ok=True)
VIDEO=ROOT/'output/video';DEST=VIDEO/'rescue_drone_final.mp4'
SECTIONS=[
 ('intro_pan','rescue_drone_intro_pan.mp4',24,'タイトル・災害救助ドローンとは'),
 ('mechanism_movie','rescue_drone_mechanism.mp4',28,'飛行制御のしくみ'),
 ('training_movie_v2','rescue_drone_training_v2_preview.mp4',14,'SmolVLAの追加学習'),
 ('demo_movie','rescue_drone_demonstration.mp4',40,'シミュレーターでの実演・青い服の人'),
 ('red_movie','rescue_drone_red_search.mp4',26,'赤い服の人を捜索'),
 ('conditions_movie','rescue_drone_visual_conditions.mp4',27,'視界が悪い環境での捜索'),
 ('ending_movie','rescue_drone_ending.mp4',30,'実機への展開・まとめ')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):return subprocess.run(args,capture_output=True,check=True)
def hashes(p):
 s=run(['ffmpeg','-v','error','-i',str(p),'-map','0:v:0','-f','framemd5','-']).stdout.decode()
 return [line.split(',')[-1].strip() for line in s.splitlines() if line and not line.startswith('#')]
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

paths=[VIDEO/s[1] for s in SECTIONS];durations=[s[2] for s in SECTIONS]
before={str(p):sha(p) for p in paths}
training=json.loads((HERE/'training_movie_v2/review.json').read_text(encoding='utf8'))
assert training['visual_review_complete'] and training['independent_transcription_matches']
assert before[str(paths[2])]==training['videos'][0]['sha256']
voicecheck=json.loads((HERE/'training_movie_v2/independent_transcription.json').read_text(encoding='utf8'))
assert voicecheck['wording_matches'] and voicecheck['audio_sha256']==sha(HERE/'training_movie_v2/dry_narration.wav')
captions=[];chapters=[];offset=0
for folder,name,duration,label in SECTIONS:
 chapters.append(dict(start_s=offset,duration_s=duration,title=label,source=name))
 for v in json.loads((HERE/folder/'voice_manifest.json').read_text(encoding='utf8')):
  assert v['start']+v['duration_s']<=duration
  captions.append(dict(start=offset+v['start'],end=offset+v['start']+v['duration_s'],text=v['text']))
 offset+=duration
assert offset==189 and all(a['end']<=b['start'] for a,b in zip(captions,captions[1:]))
transcript=OUT/'transcript_review.srt'
transcript.write_text('\n\n'.join(f'{i+1}\n{stamp(v["start"])} --> {stamp(v["end"])}\n{v["text"]}' for i,v in enumerate(captions))+'\n',encoding='utf8')
staging=OUT/'assembled.mp4'
join(paths,durations,staging,'final_with_training')
print('ASSEMBLED_189_SECONDS',flush=True)
assert all(sha(Path(p))==s for p,s in before.items())
probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(staging)]).stdout)
v=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'],int(v['nb_frames']))==(1920,1080,189*24)
assert abs(float(probe['format']['duration'])-189)<.05
assert not any(s['codec_type']=='subtitle' for s in probe['streams'])
run(['ffmpeg','-v','error','-xerror','-i',str(staging),'-f','null','-'])
print('FULL_DECODE_PASS',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 source_hashes=list(pool.map(hashes,paths))
full=hashes(staging)
assert full==sum(source_hashes,[])
print('ALL_4536_PICTURE_FRAMES_PRESERVED',flush=True)
stats_text=run(['ffmpeg','-hide_banner','-i',str(staging),'-af','loudnorm=I=-16:TP=-2:LRA=7:print_format=json','-f','null','-']).stderr.decode('utf8',errors='replace')
stats=json.loads(stats_text[stats_text.rfind('{'):stats_text.rfind('}')+1])
assert -18<float(stats['input_i'])<-14 and float(stats['input_tp'])<=-1
sheet=Image.new('RGB',(1280,1170),'#091319');draw=ImageDraw.Draw(sheet)
for i,t in enumerate([49,54,60,65,68,71]):
 raw=run(['ffmpeg','-v','error','-ss',str(t),'-i',str(staging),'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','-']).stdout
 frame=Image.fromarray(np.frombuffer(raw,dtype=np.uint8).reshape(1080,1920,3))
 x=i%2*640;y=i//2*390
 draw.text((x+10,y+3),f'{t:.1f} s',font=font(20),fill='white')
 sheet.paste(frame.resize((640,360)),(x,y+30))
sheet.save(OUT/'transitions.jpg',quality=95)
# No delivery-side SRT: this film already contains visible captions.
if DEST.with_suffix('.srt').exists():
 old=DEST.with_suffix('.srt');(OUT/'previous_sidecar.srt').write_bytes(old.read_bytes());old.unlink()
# Publish only after the new assembly passes verification. The earlier caption-fixed version remains available.
staging.replace(DEST)
report=dict(video=str(DEST),sha256=sha(DEST),duration_s=float(probe['format']['duration']),dimensions=[1920,1080],fps=24,frames=len(full),chapters=chapters,source_sha256=before,full_decode=True,all_source_picture_frames_preserved=True,narration_overlap=False,subtitle_delivery='Burned-in captions only; no external SRT beside the video',transcript_review_file=str(transcript),loudness=stats,training_voice_model='gpt-4o-mini-tts-2025-12-15',training_voice='marin',training_asr_verified=True,animation='Fixed geometry with narration-led emphasis and teacher-data pairing connectors',visual_review_complete=False,audio_listening_review=False)
DEST.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('FINAL_WITH_TRAINING_COMPLETE',DEST,flush=True)
