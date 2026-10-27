"""Verify the completed film, revised pronunciation, preserved scenes and closing."""
from ending_movie import *
def run(a):return subprocess.run(a,capture_output=True,check=True)
def hashes(p):
 s=run(['ffmpeg','-v','error','-i',str(p),'-map','0:v:0','-f','framemd5','-']).stdout.decode()
 return [l.split(',')[-1].strip() for l in s.splitlines() if l and not l.startswith('#')]
m=Movie();source=json.loads((OUT/'source_evidence.json').read_text())
assert all(sha(Path(p))==v for p,v in source['source_segments_sha256'].items())
assert source['hardware_design_sha256']==sha(ROOT/'hardware_design.json')
asr=json.loads((OUT/'independent_transcription.json').read_text(encoding='utf8'))
assert asr['wording_matches'] and asr['audio_sha256']==sha(OUT/'dry_narration.wav')
powder=json.loads((HERE/'conditions_movie/generation_manifest.json').read_text(encoding='utf8'))[0]
assert 'ふんじん' in powder['api_input_text'] and 'こなじん' not in powder['api_input_text']
assert powder['sha256']==sha(HERE/'conditions_movie/voice_00.wav')
powder_asr=json.loads((HERE/'conditions_movie/independent_transcription.json').read_text(encoding='utf8'))
assert powder_asr['wording_matches'] and powder_asr['audio_sha256']==sha(HERE/'conditions_movie/dry_narration.wav')
assert all(v['duration_s']==v['original_duration_s'] for v in m.voices)
assert all(a['start']+a['duration_s']<b['start'] for a,b in zip(m.voices,m.voices[1:]))
assert m.voices[1]['start']+m.voices[1]['duration_s']<15
assert m.voices[-1]['start']+m.voices[-1]['duration_s']<DURATION-2
reports=[]
for p,duration in [(DEST,30),(PREFIX,145),(COMBINED,175)]:
 probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]).stdout)
 v=next(s for s in probe['streams'] if s['codec_type']=='video')
 assert (v['width'],v['height'])==(1920,1080) and int(v['nb_frames'])==duration*FPS
 assert abs(float(probe['format']['duration'])-duration)<.1
 run(['ffmpeg','-v','error','-xerror','-i',str(p),'-f','null','-'])
 loud=run(['ffmpeg','-hide_banner','-i',str(p),'-af','loudnorm=I=-16:TP=-2:LRA=7:print_format=json','-f','null','-']).stderr.decode('utf8',errors='replace')
 stats=json.loads(loud[loud.rfind('{'):loud.rfind('}')+1]);assert -18<float(stats['input_i'])<-14 and float(stats['input_tp'])<=-1
 reports.append(dict(video=str(p),sha256=sha(p),duration_s=float(probe['format']['duration']),dimensions=[1920,1080],fps=FPS,frames=int(v['nb_frames']),full_decode=True,loudness=stats))
 print('DECODE_QA',p.name,flush=True)
parts=[hashes(p) for p in PARTS];ending=hashes(DEST);prefix=hashes(PREFIX);full=hashes(COMBINED)
expected=sum(parts,[]);assert prefix==expected and full==expected+ending
checks=[];sheet=Image.new('RGB',(1280,1170),BG)
for i,t in enumerate([4,11,18,23,27.8,29.5]):
 raw=run(['ffmpeg','-v','error','-ss',str(t),'-i',str(DEST),'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','-']).stdout
 got=np.frombuffer(raw,dtype=np.uint8).reshape(1080,1920,3)
 mae=float(np.abs(got.astype(float)-np.asarray(m.frame(t),dtype=float)).mean());assert mae<6
 checks.append(dict(time_s=t,source_mae=mae));x=i%2*640;y=i//2*390
 text(sheet,x+10,y+4,f'{t:.1f} s',19);sheet.paste(Image.fromarray(got).resize((640,360)),(x,y+30))
sheet.save(OUT/'encoded_contact_sheet.jpg',quality=95)
# Export exact narration timing as a separate accessibility/review artifact.
sections=[('intro_pan',0),('mechanism_movie',24),('demo_movie',52),('red_movie',92),('conditions_movie',118),('ending_movie',145)]
captions=[]
for folder,offset in sections:
 for v in json.loads((HERE/folder/'voice_manifest.json').read_text(encoding='utf8')):
  captions.append(dict(start=offset+v['start'],end=offset+v['start']+v['duration_s'],text=v['text']))
captions.sort(key=lambda v:v['start'])
assert all(a['end']<=b['start'] for a,b in zip(captions,captions[1:]))
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
# Captions are already burned into the movie. Keep the transcript out of the
# delivery directory so media players cannot automatically overlay it again.
transcript=OUT/'transcript_review.srt'
transcript.write_text('\n\n'.join(f'{i+1}\n{stamp(v["start"])} --> {stamp(v["end"])}\n{v["text"]}' for i,v in enumerate(captions))+'\n',encoding='utf8')
for report,p in zip(reports,[DEST,PREFIX,COMBINED]):
 report.update(approved_picture_segments_preserved=True,powder_reading_corrected_to='ふんじん',pronunciation_method='Explicit hiragana TTS input; independent transcription of wording',ending_independent_asr_match=True,voice_overlap=False,voice_time_stretch=False,music_only_tail_s=2.7,hardware_is_unverified_proposal=True,source_frame_checks=checks,visual_review_complete=False,audio_listening_review=False,source_evidence=str(OUT/'source_evidence.json'))
 if p==COMBINED:report.update(chapters_s=[0,24,52,92,118,145,160,175],transcript_review_file=str(transcript),subtitle_delivery='Burned-in captions only; no auto-loaded sidecar')
 p.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'final_qa.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
print('FINAL_QA_PASS',len(full),'frames',flush=True)
