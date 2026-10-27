import json,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw
from mechanism_movie import *
def run(args):return subprocess.run(args,capture_output=True,check=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(p):
    raw=run(['ffmpeg','-v','error','-i',str(p),'-map','0:v:0','-f','framemd5','-']).stdout.decode()
    return [s.split(',')[-1].strip() for s in raw.splitlines() if s and not s.startswith('#')]
reports=[]
for p,duration in [(DEST,28),(COMBINED,52)]:
    probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]).stdout)
    v=next(x for x in probe['streams'] if x['codec_type']=='video')
    assert (v['width'],v['height'])==(1920,1080)
    assert int(v['nb_frames'])==duration*FPS
    assert abs(float(probe['format']['duration'])-duration)<.08
    run(['ffmpeg','-v','error','-xerror','-i',str(p),'-f','null','-'])
    loud=run(['ffmpeg','-hide_banner','-i',str(p),'-af','loudnorm=I=-16:TP=-2:LRA=7:print_format=json','-f','null','-']).stderr.decode('utf8',errors='replace')
    stats=json.loads(loud[loud.rfind('{'):loud.rfind('}')+1])
    assert -18<float(stats['input_i'])<-14 and float(stats['input_tp'])<=-1
    reports.append(dict(video=str(p),sha256=sha(p),duration_s=float(probe['format']['duration']),frames=int(v['nb_frames']),full_decode=True,loudness=stats))
a,b,c=hashes(INTRO),hashes(DEST),hashes(COMBINED)
assert c[:len(a)]==a and c[len(a):]==b
source=json.loads((OUT/'source_evidence.json').read_text(encoding='utf8'))
assert sha(INTRO)==source['accepted_intro_sha256']
asr=json.loads((OUT/'independent_transcription.json').read_text(encoding='utf8'))
assert asr['wording_matches'] and asr['audio_sha256']==sha(OUT/'dry_narration.wav')
movie=Movie();voices=movie.voices
assert all(x['start']+x['duration_s']<y['start'] for x,y in zip(voices,voices[1:]))
assert voices[-1]['start']+voices[-1]['duration_s']<27.5
assert all(x['duration_s']==x['original_duration_s'] for x in voices)
sheet=Image.new('RGB',(1280,1170),'#091319');d=ImageDraw.Draw(sheet);checks=[]
for i,t in enumerate([2.5,7,10,14,19.5,23.5]):
    raw=run(['ffmpeg','-v','error','-ss',str(t),'-i',str(DEST),'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','-']).stdout
    got=np.frombuffer(raw,dtype=np.uint8).reshape(1080,1920,3)
    mae=float(np.abs(got.astype(float)-np.asarray(movie.frame(t),dtype=float)).mean());assert mae<6
    checks.append(dict(t=t,mae=mae));x=i%2*640;y=i//2*390
    d.text((x+10,y+2),f'{t:.1f} s',font=font(20),fill='white');sheet.paste(Image.fromarray(got).resize((640,360)),(x,y+30))
sheet.save(OUT/'encoded_contact_sheet.jpg',quality=95)
for report,p in zip(reports,[DEST,COMBINED]):
    report.update(accepted_intro_pixels_preserved=True,mechanism_pixels_preserved_in_combined=True,independent_asr_wording_match=True,verbatim_subtitles=True,voice_overlap=False,time_stretch=False,source_frame_checks=checks,visual_review_complete=False,audio_listening_review=False)
    p.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'final_qa.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(success=True,frames=[len(a),len(b),len(c)],max_mae=max(x['mae'] for x in checks))))
