import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from finalize_premium_video import run,loudness,stamp
from edit_movie import Record
HERE=Path(__file__).resolve().parent;OUT=HERE/'movie'
plan=json.loads((OUT/'plan.json').read_text(encoding='utf8'))
target=ROOT/'output/video/rescue_drone_presentation_v3.mp4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not target.exists()
for condition,files in plan['source_sha256'].items():
    for file,h in files.items():assert sha(Path(plan['records'])/(condition+'_blue')/file)==h
before=loudness(OUT/'soundtrack.wav')
af=('loudnorm=I=-16:TP=-2:LRA=10:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=false:print_format=json').format(**before)
run(['ffmpeg','-hide_banner','-i',str(OUT/'search_presentation_silent.mp4'),'-i',str(OUT/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af',af,'-c:a','aac','-b:a','256k','-ar','48000','-t',str(plan['duration_s']),'-movflags','+faststart','-metadata','title=災害救助ドローンの開発','-metadata','comment=Actual simulated search flights. Original VLA camera inputs. External cameras reconstructed from unchanged flight logs. Proposed real hardware not tested.',str(target)])
probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(target)]).stdout)
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(1920,1080,'30/1',plan['frames'])
assert a['sample_rate']=='48000' and a['channels']==2
decoded=run(['ffmpeg','-v','error','-xerror','-i',str(target),'-f','null','-']);assert not decoded.stderr.strip()
times=set(range(0,plan['duration_s'],2))
for s in plan['timeline'][1:]:times.update([s['start']-.1,s['start']+.2])
demo=next(s for s in plan['timeline'] if s['name']=='demo')
score=plan['scores']['clear']
for event in [score['discovery_time_s'],score['notification_time_s']]:
    t=demo['start']+(event-16)/2;times.update([t-.15,t+.15])
frames=sorted(set(round(t*30) for t in times));times=[n/30 for n in frames]
dest=OUT/'final_qa';dest.mkdir(exist_ok=False)
selection='+'.join(f'eq(n\\,{i})' for i in frames)
run(['ffmpeg','-v','error','-xerror','-i',str(target),'-vf',f'select={selection}','-fps_mode','vfr',str(dest/'frame_%03d.png')])
images=sorted(dest.glob('frame_*.png'));assert len(images)==len(times)
sheets=[];font=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',20)
for start in range(0,len(images),6):
    sheet=Image.new('RGB',(1440,1302),'#091218');d=ImageDraw.Draw(sheet)
    for j,p in enumerate(images[start:start+6]):
        x=j%2*720;y=j//2*434;sheet.paste(Image.open(p).resize((720,405)),(x,y));d.text((x+12,y+408),f'{times[start+j]:06.2f} s',font=font,fill='#c7d1d4')
    file=dest/f'sheet_{start//6:02}.jpg';sheet.save(file,quality=94);sheets.append(str(file))
records={c:Record(Path(plan['records'])/(c+'_blue')) for c in plan['scores']}
checks=[]
for i,t in enumerate(times):
    section=next(s for s in plan['timeline'] if s['start']<=t<s['end'])
    if section['name'] not in ('demo','conditions'):continue
    u=t-section['start'];name='demo' if section['name']=='demo' else ['fog_light','fog_dense','dust'][min(2,int(u/8))]
    if section['name']=='conditions':u=u%8
    segment=next(s for s in plan['segments'] if s['name']==name);condition=segment['condition'];r=records[condition]
    moment=min(segment['sim_end'],segment['sim_start']+u*2);_,row,packet,img=r.at(moment)
    assert img is not None
    found=row['t']>=r.score['discovery_time_s']
    enlarged=name=='demo' and not found and row['phase'] in ('hover','right','confirm')
    rectangle=[48,260,944,932] if enlarged else plan['panel_rectangle']
    size=(896,672) if enlarged else (512,384)
    actual=np.asarray(Image.open(images[i]).convert('RGB').crop(tuple(rectangle)),dtype=float)
    expected=np.asarray(img.resize(size,Image.Resampling.NEAREST),dtype=float)
    mae=float(np.abs(actual-expected).mean());assert mae<8,(t,mae)
    checks.append(dict(video_time=t,condition=condition,input_sha256=packet['image_sha256'],pixel_mae=mae,rectangle=rectangle))
assert {r['condition'] for r in checks}==set(records)
voices=json.loads((OUT/'voice_manifest.json').read_text(encoding='utf8'));assert min(v['start'] for v in voices)>=4
srt=[]
for i,c in enumerate(voices):srt.extend([str(i+1),stamp(c['start'])+' --> '+stamp(c['start']+c['duration_s']+.1),c['caption'],''])
(target.with_suffix('.srt')).write_text('\n'.join(srt),encoding='utf8')
after=loudness(target);assert abs(float(after['input_i'])+16)<.8 and float(after['input_tp'])<=-1.4
qa=dict(video_sha256=sha(target),duration_s=plan['duration_s'],frames=plan['frames'],full_decode=True,title_music_only=True,
        input_panels=dict(count=len(checks),max_mae=max(c['pixel_mae'] for c in checks),checks=checks),loudness=after,
        contact_sheets=sheets,extracted_times_s=times,visual_review_complete=False,audio_listening_review=False)
(OUT/'final_qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(video_sha256=qa['video_sha256'],duration_s=plan['duration_s'],input_checks=len(checks),max_mae=qa['input_panels']['max_mae']),indent=2))
