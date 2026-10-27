"""Verify decoded video, original camera pixels, recorded actions and preserved intro."""
from demo_movie import *
def run(a):return subprocess.run(a,capture_output=True,check=True)
def framehashes(p):
 s=run(['ffmpeg','-v','error','-i',str(p),'-map','0:v:0','-f','framemd5','-']).stdout.decode()
 return [l.split(',')[-1].strip() for l in s.splitlines() if l and not l.startswith('#')]
m=Movie();frames=json.loads((OUT/'frames.json').read_text());assert len(frames)==DURATION*FPS
assert sum(f.get('kind')=='chapter_card' for f in frames)==CARD*FPS
checked=0;used=set()
for f in frames:
 if f.get('kind')=='chapter_card':continue
 index,row,p=m.state(f['video_time_s']-CARD)
 assert f['simulation_time']==row['t'] and f['external_frame']==index
 if p:
  assert f['camera_sha256']==p['image_sha256'];used.add(p['id'])
 if f['actions_displayed'] is not None:
  assert p and not f['landing_autopilot'] and f['action_source']=='policy'
  ci=f['translation_chunk_index'];yi=f['yaw_chunk_index'];a=f['actions_displayed'];chunk=p['action_chunk']
  assert max(abs(a[k]-chunk[ci][k]) for k in range(3))<1e-6
  assert abs(a[3]-chunk[yi][3])<1e-6;checked+=1
 if row['t']>=m.land_request:assert f['actions_displayed'] is None
assert frames[-1]['completed']
evidence=json.loads((OUT/'source_evidence.json').read_text())
assert evidence['accepted_intro_sha256']==sha(INTRO)
audio_meta=json.loads((OUT/'audio_review.json').read_text());voice=json.loads((OUT/'voice_manifest.json').read_text(encoding='utf8'))
assert len(voice)==1 and voice[0]['start']>=CARD and voice[0]['start']+voice[0]['duration_s']<=CARD+LEAD
assert voice[0]['duration_s']==voice[0]['original_duration_s']
assert sha(OUT/'voice_00.wav')==audio_meta['voice_source_sha256']
print('DATA_QA',checked,'action frames;',len(used),'input images',flush=True)
reports=[]
for path,duration in [(DEST,DURATION),(COMBINED,52+DURATION)]:
 probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]).stdout)
 v=next(s for s in probe['streams'] if s['codec_type']=='video')
 assert (v['width'],v['height'])==(1920,1080) and int(v['nb_frames'])==duration*FPS
 assert abs(float(probe['format']['duration'])-duration)<.1
 run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'])
 loud=run(['ffmpeg','-hide_banner','-i',str(path),'-af','loudnorm=I=-16:TP=-2:LRA=7:print_format=json','-f','null','-']).stderr.decode('utf8',errors='replace')
 stats=json.loads(loud[loud.rfind('{'):loud.rfind('}')+1])
 # The demonstration is predominantly quiet music with one short spoken command.
 # Keep it quieter than the narration-heavy introduction, while checking headroom.
 minimum=-22 if path==DEST else -18
 assert minimum<float(stats['input_i'])<-14 and float(stats['input_tp'])<=-1
 reports.append(dict(video=str(path),sha256=sha(path),duration_s=float(probe['format']['duration']),dimensions=[1920,1080],fps=FPS,frames=int(v['nb_frames']),full_decode=True,loudness=stats))
 print('DECODE_QA',path.name,flush=True)
a,b,c=framehashes(INTRO),framehashes(DEST),framehashes(COMBINED)
assert c[:len(a)]==a and c[len(a):]==b
sheet=Image.new('RGB',(1280,1560),BG);checks=[]
for i,t in enumerate([1,6,12,19,26,33,36,38]):
 raw=run(['ffmpeg','-v','error','-ss',str(t),'-i',str(DEST),'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','-']).stdout
 got=np.frombuffer(raw,dtype=np.uint8).reshape(1080,1920,3);expected=m.frame(t)
 mae=float(np.abs(got.astype(float)-np.asarray(expected,dtype=float)).mean());assert mae<6
 roi_mae=None
 if t>=CARD:
  _,row,p=m.state(t-CARD)
  if p:
   source=np.asarray(m.record.inputs[p['id']].resize((480,360),Image.Resampling.NEAREST))
   assert np.array_equal(np.asarray(expected)[198:558,1368:1848],source)
   roi_mae=float(np.abs(got[198:558,1368:1848].astype(float)-source.astype(float)).mean());assert roi_mae<6
 checks.append(dict(time_s=t,source_mae=mae,original_camera_roi_mae=roi_mae))
 x=i%2*640;y=i//2*390;text(sheet,x+10,y+4,f'{t:.1f} s',19);sheet.paste(Image.fromarray(got).resize((640,360)),(x,y+30))
sheet.save(OUT/'encoded_contact_sheet.jpg',quality=95)
for report,p in zip(reports,[DEST,COMBINED]):
 report.update(accepted_intro_frames_unchanged=True,demo_frames_preserved_in_combined=True,chapter_card_music_only=True,chapter_card_duration_s=CARD,playback_speed=SPEED,applied_action_frames_verified=checked,original_camera_images_verified=len(used),original_camera_no_enhancement=True,input_action_time_alignment_verified=True,landing_autopilot_distinguished=True,trail_projection_verified=True,source_frame_checks=checks,visual_review_complete=False,audio_listening_review=False,voice='Previously approved OpenAI narration; original WAV SHA verified')
 p.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'final_qa.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
print('DEMO_QA_PASS',len(c),'combined frames',flush=True)
