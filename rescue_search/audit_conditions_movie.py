"""Check the visual-condition edit against immutable observations and action chunks."""
from conditions_movie import *
def run(a):return subprocess.run(a,capture_output=True,check=True)
def hashes(p):
 s=run(['ffmpeg','-v','error','-i',str(p),'-map','0:v:0','-f','framemd5','-']).stdout.decode()
 return [l.split(',')[-1].strip() for l in s.splitlines() if l and not l.startswith('#')]
m=Movie();frames=json.loads((OUT/'frames.json').read_text());assert len(frames)==FPS*DURATION
checked=0;used={c:set() for c in CONDITIONS};counts={c:0 for c in CONDITIONS}
for f in frames:
 if f['kind']!='flight_excerpt':continue
 c=f['condition'];condition=m.movies[c];counts[c]+=1
 part=CONDITIONS.index(c);u=f['video_time_s']-2-6*part
 idx,row,p=condition.state(base.LEAD+u)
 assert f['simulation_time']==row['t'] and f['external_frame']==idx
 assert p and f['camera_sha256']==p['image_sha256'];used[c].add(p['id'])
 if f['actions'] is not None:
  a=f['actions'];ci=f['translation_chunk_index'];yi=f['yaw_chunk_index'];chunk=p['action_chunk']
  assert max(abs(a[k]-chunk[ci][k]) for k in range(3))<1e-6 and abs(a[3]-chunk[yi][3])<1e-6
  checked+=1
assert all(n==6*FPS for n in counts.values())
asr=json.loads((OUT/'independent_transcription.json').read_text(encoding='utf8'))
assert asr['wording_matches'] and asr['audio_sha256']==sha(OUT/'dry_narration.wav')
assert all(v['duration_s']==v['original_duration_s'] for v in m.voices)
assert m.voices[0]['start']>=2 and m.voices[-1]['start']+m.voices[-1]['duration_s']<DURATION-.5
source=json.loads((OUT/'source_evidence.json').read_text());assert source['accepted_intro_sha256']==sha(INTRO)
print('CONDITION_DATA_QA',checked,'action frames;', {c:len(x) for c,x in used.items()},flush=True)
reports=[]
for path,duration in [(DEST,DURATION),(COMBINED,90+DURATION)]:
 probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]).stdout)
 v=next(s for s in probe['streams'] if s['codec_type']=='video')
 assert (v['width'],v['height'])==(1920,1080) and int(v['nb_frames'])==duration*FPS
 assert abs(float(probe['format']['duration'])-duration)<.1
 run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'])
 loud=run(['ffmpeg','-hide_banner','-i',str(path),'-af','loudnorm=I=-16:TP=-2:LRA=7:print_format=json','-f','null','-']).stderr.decode('utf8',errors='replace')
 stats=json.loads(loud[loud.rfind('{'):loud.rfind('}')+1]);assert -18<float(stats['input_i'])<-14 and float(stats['input_tp'])<=-1
 reports.append(dict(video=str(path),sha256=sha(path),duration_s=float(probe['format']['duration']),dimensions=[1920,1080],fps=FPS,frames=int(v['nb_frames']),full_decode=True,loudness=stats))
 print('DECODE_QA',path.name,flush=True)
a,b,c=hashes(INTRO),hashes(DEST),hashes(COMBINED)
assert c[:len(a)]==a and c[len(a):]==b
sheet=Image.new('RGB',(1280,1170),BG);checks=[]
for i,t in enumerate([1,5,11,17,21,24]):
 raw=run(['ffmpeg','-v','error','-ss',str(t),'-i',str(DEST),'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','-']).stdout
 got=np.frombuffer(raw,dtype=np.uint8).reshape(1080,1920,3);expected=m.frame(t)
 mae=float(np.abs(got.astype(float)-np.asarray(expected,dtype=float)).mean());assert mae<6
 roi_mae=None
 if 2<=t<20:
  part=int((t-2)/6);condition=m.movies[CONDITIONS[part]];_,row,p=condition.state(base.LEAD+t-2-6*part)
  original=np.asarray(condition.record.inputs[p['id']].resize((480,360),Image.Resampling.NEAREST))
  assert np.array_equal(np.asarray(expected)[198:558,1368:1848],original)
  roi_mae=float(np.abs(got[198:558,1368:1848].astype(float)-original.astype(float)).mean());assert roi_mae<6
 checks.append(dict(time_s=t,source_mae=mae,original_camera_roi_mae=roi_mae))
 x=i%2*640;y=i//2*390;text(sheet,x+10,y+4,f'{t:.1f} s',19);sheet.paste(Image.fromarray(got).resize((640,360)),(x,y+30))
sheet.save(OUT/'encoded_contact_sheet.jpg',quality=95)
for report,p in zip(reports,[DEST,COMBINED]):
 report.update(accepted_intro_frames_unchanged=True,section_frames_preserved_in_combined=True,audio_join='Trimmed encoder padding before concatenation; AAC re-encoded',chapter_music_only=True,playback_speed=2,excerpts_explicitly_labelled=True,action_frames_verified=checked,input_images_verified={c:len(x) for c,x in used.items()},original_camera_no_enhancement=True,independent_asr_match=True,verbatim_subtitles=True,voice_time_stretch=False,all_four_condition_results_verified=True,trials_per_condition=1,same_checkpoint_verified=m.checkpoint,source_frame_checks=checks,visual_review_complete=False,audio_listening_review=False)
 p.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'final_qa.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
print('CONDITIONS_QA_PASS',len(c),'combined frames',flush=True)
