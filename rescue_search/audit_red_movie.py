"""Audit the fresh red-person run and the inserted presentation segment."""
from red_movie import *
def run(a):return subprocess.run(a,capture_output=True,check=True)
def hashes(p):
 s=run(['ffmpeg','-v','error','-i',str(p),'-map','0:v:0','-f','framemd5','-']).stdout.decode()
 return [l.split(',')[-1].strip() for l in s.splitlines() if l and not l.startswith('#')]
m=Movie();r=m.record
assert r.result['profile']=='red' and r.result['upper_instruction']=='赤い服の人を探して'
assert r.score['success'] and all(r.score['checks'].values())
assert r.score['physical']['goal_holds']['red']['physical_hold']['duration_s']>=3
assert r.score['physical']['goal_holds']['blue']['physical_hold']['duration_s']==0
blue=json.loads((HERE/'runs/eval03/manifest.json').read_text(encoding='utf8'))
red=json.loads((HERE/'runs/eval_red01/manifest.json').read_text(encoding='utf8'))
assert blue['checkpoint_sha256']==red['checkpoint_sha256']
assert blue['source_sha256']==red['source_sha256'] and blue['scene_conditions']==red['scene_conditions']
assert sha(r.path/'search_score.json')==PLAN['search_score_sha256']
frames=json.loads((OUT/'frames.json').read_text());assert len(frames)==FPS*DURATION
checked=0;used=set()
for f in frames:
 idx,row,p=m.state(base.LEAD+f['video_time_s']-LEAD)
 assert f['external_frame']==idx and f['simulation_time']==row['t']
 if p:assert f['camera_sha256']==p['image_sha256'];used.add(p['id'])
 if f['actions'] is not None:
  assert p and not f['landing_autopilot'] and f['action_source']=='policy'
  a=f['actions'];ci=f['translation_chunk_index'];yi=f['yaw_chunk_index'];c=p['action_chunk']
  assert max(abs(a[k]-c[ci][k]) for k in range(3))<1e-6 and abs(a[3]-c[yi][3])<1e-6;checked+=1
 if row['t']>=m.land_request:assert f['actions'] is None
assert frames[-1]['completed']
asr=json.loads((OUT/'independent_transcription.json').read_text(encoding='utf8'))
assert asr['wording_matches'] and asr['audio_sha256']==sha(OUT/'dry_narration.wav')
voice=json.loads((OUT/'voice_manifest.json').read_text(encoding='utf8'))
assert len(voice)==1 and voice[0]['start']+voice[0]['duration_s']<LEAD
source=json.loads((OUT/'source_evidence.json').read_text())
assert all(sha(Path(p))==v for p,v in source['accepted_files_sha256'].items())
print('RED_DATA_QA',checked,'action frames;',len(used),'input images',flush=True)
reports=[]
for path,duration in [(DEST,DURATION),(COMBINED,117+DURATION)]:
 probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]).stdout)
 v=next(s for s in probe['streams'] if s['codec_type']=='video')
 assert (v['width'],v['height'])==(1920,1080) and int(v['nb_frames'])==duration*FPS
 assert abs(float(probe['format']['duration'])-duration)<.1
 run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'])
 loud=run(['ffmpeg','-hide_banner','-i',str(path),'-af','loudnorm=I=-16:TP=-2:LRA=7:print_format=json','-f','null','-']).stderr.decode('utf8',errors='replace')
 stats=json.loads(loud[loud.rfind('{'):loud.rfind('}')+1]);minimum=-22 if path==DEST else -18
 assert minimum<float(stats['input_i'])<-14 and float(stats['input_tp'])<=-1
 reports.append(dict(video=str(path),sha256=sha(path),duration_s=float(probe['format']['duration']),dimensions=[1920,1080],fps=FPS,frames=int(v['nb_frames']),full_decode=True,loudness=stats))
 print('DECODE_QA',path.name,flush=True)
a,b,c,joined=hashes(INTRO),hashes(DEST),hashes(CONDITIONS),hashes(COMBINED)
assert joined==a+b+c
sheet=Image.new('RGB',(1280,1170),BG);checks=[]
for i,t in enumerate([2,6,10.25,17,19.5,24.5]):
 raw=run(['ffmpeg','-v','error','-ss',str(t),'-i',str(DEST),'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','-']).stdout
 got=np.frombuffer(raw,dtype=np.uint8).reshape(1080,1920,3);expected=m.frame(t)
 mae=float(np.abs(got.astype(float)-np.asarray(expected,dtype=float)).mean());assert mae<6
 _,row,p=m.state(base.LEAD+t-LEAD);roi_mae=None
 if p:
  original=np.asarray(r.inputs[p['id']].resize((480,360),Image.Resampling.NEAREST))
  assert np.array_equal(np.asarray(expected)[198:558,1368:1848],original)
  roi_mae=float(np.abs(got[198:558,1368:1848].astype(float)-original.astype(float)).mean());assert roi_mae<6
 checks.append(dict(time_s=t,source_mae=mae,original_camera_roi_mae=roi_mae))
 x=i%2*640;y=i//2*390;text(sheet,x+10,y+4,f'{t:.1f} s',19);sheet.paste(Image.fromarray(got).resize((640,360)),(x,y+30))
sheet.save(OUT/'encoded_contact_sheet.jpg',quality=95)
for report,p in zip(reports,[DEST,COMBINED]):
 report.update(accepted_intro_and_conditions_frames_unchanged=True,same_model_code_scene_as_blue=True,new_red_run_success=True,red_stop_s=r.score['physical']['goal_holds']['red']['physical_hold']['duration_s'],new_training=False,action_frames_verified=checked,original_input_images_verified=len(used),original_camera_no_enhancement=True,independent_asr_match=True,source_frame_checks=checks,visual_review_complete=False,audio_listening_review=False,source_evidence=str(OUT/'source_evidence.json'))
 p.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'final_qa.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
print('RED_QA_PASS',len(joined),'combined frames',flush=True)
