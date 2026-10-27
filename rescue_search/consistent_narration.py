"""Normalize sentence pace, retain recorded flights, and resynchronize captions."""
import os,sys,json,math,hashlib,wave,subprocess,importlib,concurrent.futures
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import imageio.v2 as imageio
from narration_pace_audit import READINGS,mora
from demo_movie import text,font,smooth,BG,WHITE
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);HERE=Path(__file__).resolve().parent
OUT=HERE/'narration_consistent';OUT.mkdir(exist_ok=True)
VIDEO=ROOT/'output/video';FPS=24
FOLDERS=['intro_pan','mechanism_movie','training_movie_v2','demo_movie','red_movie','conditions_movie','ending_movie']
FILES=['rescue_drone_intro_pan.mp4','rescue_drone_mechanism.mp4','rescue_drone_training_v2_preview.mp4','rescue_drone_demonstration.mp4','rescue_drone_red_search.mp4','rescue_drone_visual_conditions.mp4','rescue_drone_ending.mp4']
BASE_DURATION=[24,28,14,40,26,27,30]
NEW_TEXT=['SmolVLAを飛行制御に対応させるため、追加学習を行っています。','移動や旋回などの動作を定義し、画像や指示、機体の状態と対応付けています。']
NEW_LINES=[['SmolVLAを飛行制御に対応させるため、','追加学習を行っています。'],['移動や旋回などの動作を定義し、','画像や指示、機体の状態と対応付けています。']]
READINGS['training_movie_v2']=['すもーるぶいえるえーをひこうせいぎょにたいおうさせるため、ついかがくしゅうをおこなっています。',READINGS['training_movie_v2'][1]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(a):return subprocess.run(a,capture_output=True,check=True)
def wav_duration(p):
 with wave.open(str(p),'rb') as w:return w.getnframes()/w.getframerate()
def prepare(indices=None):
 verified=json.loads((OUT/'new_training/asr.json').read_text(encoding='utf8'));assert verified['wording_matches']
 source_manifest=json.loads((OUT/'new_training/manifest.json').read_text(encoding='utf8'))
 sections=[];allclips=[]
 for sec,(folder,file,duration) in enumerate(zip(FOLDERS,FILES,BASE_DURATION)):
  if indices is not None and sec not in indices:continue
  dest=OUT/folder;dest.mkdir(exist_ok=True)
  old=json.loads((HERE/folder/'voice_manifest.json').read_text(encoding='utf8'))
  clips=[]
  for i,(v,reading) in enumerate(zip(old,READINGS[folder])):
   source=(OUT/'new_training'/f'voice_{i:02}.wav') if sec==2 else HERE/folder/v['file']
   replacement_text=None
   if sec==6 and i==0 and (OUT/'new_ending/manifest.json').exists():
    assert json.loads((OUT/'new_ending/asr.json').read_text(encoding='utf8'))['wording_matches']
    source=OUT/'new_ending/voice_00.wav'
    replacement_text=json.loads((OUT/'new_ending/manifest.json').read_text(encoding='utf8'))[0]['text']
    reading='じっきへのてんかいをみすえ、じつざいするこがたどろーんとかめら、せいぎょようぱそこんをくみあわせたこうせいにしています。'
   original=wav_duration(source)
   # Use a shared pronunciation-aware pace; retain brief punctuation pauses.
   target=round(mora(reading)/6.8+reading.count('、')*.12+.18,3)
   ratio=original/target
   assert .75<ratio<1.30,(folder,i,ratio)
   target_file=dest/f'voice_{i:02}.wav'
   run(['ffmpeg','-v','error','-y','-i',str(source),'-af',f'atempo={ratio:.8f}', '-ar','24000','-ac','1',str(target_file)])
   actual=wav_duration(target_file)
   assert abs(actual-target)<.08
   clip=dict(index=i,start=v['start'],max_s=actual+.1,text=NEW_TEXT[i] if sec==2 else v['text'],caption=NEW_TEXT[i] if sec==2 else v['text'],file=target_file.name,duration_s=actual,original_duration_s=original,source=str(source),source_sha256=sha(source),tempo_factor=ratio,reading=reading,mora=mora(reading),target_duration_s=target,output_sha256=sha(target_file))
   if replacement_text:clip.update(text=replacement_text,caption=replacement_text)
   clips.append(clip);allclips.append(dict(section=folder,**clip))
  if sec in [1,2]:
   at=1. if sec==1 else .7
   for clip in clips:clip['start']=at;at+=clip['duration_s']+.5
   duration=max(duration,math.ceil(at+.7))
  elif sec==6:
   clips[1]['start']=max(clips[1]['start'],clips[0]['start']+clips[0]['duration_s']+.4)
   hardware_end=max(15,math.ceil(clips[1]['start']+clips[1]['duration_s']+.4))
   for clip in clips[2:]:clip['start']+=hardware_end-15
   clips[3]['start']=max(clips[3]['start'],clips[2]['start']+clips[2]['duration_s']+.4)
   duration=max(duration,math.ceil(clips[3]['start']+clips[3]['duration_s']+2.5))
  assert all(a['start']+a['duration_s']<b['start'] for a,b in zip(clips,clips[1:])),folder
  assert clips[-1]['start']+clips[-1]['duration_s']<duration-.4,folder
  (dest/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
  # Mixer uses normalized WAVs directly and does not squeeze speech to fit video.
  sys.path.insert(0,str(ROOT));import make_rescue_presentation_audio as mixer
  mixer.TMP=dest;mixer.PLAN=dict(duration_s=duration,flights=[],timeline=[dict(start=0)]+([dict(start=4)] if sec==0 else []));mixer.mix()
  voices=json.loads((dest/'voice_manifest.json').read_text(encoding='utf8'))
  assert all(abs(v['duration_s']-c['duration_s'])<.001 for v,c in zip(voices,clips))
  sections.append(dict(folder=folder,source_video=str(VIDEO/file),duration_s=duration,voices=voices,old_voices=old,render_file=str(dest/'section.mp4'),hardware_end_s=hardware_end if sec==6 else None))
  print('PACE_READY',folder,[(round(c['tempo_factor'],3),round(c['duration_s'],2),round(c['start'],2)) for c in clips],duration,flush=True)
 if indices is not None:
  prior=json.loads((OUT/'plan.json').read_text(encoding='utf8'))
  sections=[next((s for s in sections if s['folder']==p['folder']),p) for p in prior]
  oldaudit=json.loads((OUT/'pace_audit.json').read_text(encoding='utf8'))['clips']
  allclips=[c for c in oldaudit if FOLDERS.index(c['section']) not in indices]+allclips
 (OUT/'plan.json').write_text(json.dumps(sections,ensure_ascii=False,indent=2),encoding='utf8')
 (OUT/'pace_audit.json').write_text(json.dumps(dict(method='Pronunciation-aware sentence durations; 6.8 mora/s plus punctuation allowances; pitch-preserving ffmpeg atempo',clips=allclips),ensure_ascii=False,indent=2),encoding='utf8')

def render_section(index):
 sections=json.loads((OUT/'plan.json').read_text(encoding='utf8'));sec=sections[index]
 folder=sec['folder'];duration=sec['duration_s'];voices=sec['voices'];dest=Path(sec.get('work_dir',str(OUT/folder)))
 if index in [3,4]:silent=Path(sec['source_video'])
 else:
  if index==0:
   import intro_pan as mod
   lines=[c[2] for c in mod.CAPTIONS]
   mod.base.CAPTIONS=[(v['start'],v['start']+v['duration_s'],line) for v,line in zip(voices,lines)]
   movie=mod.Intro();frame=movie.frame
  elif index==2:
   import training_movie_v2 as mod
   mod.OUT=dest;mod.STARTS=[v['start'] for v in voices];mod.DURATION=duration;mod.CAPTIONS=sec.get('caption_lines',NEW_LINES)
   frame=mod.make_frame()
  else:
   mod=importlib.import_module(sec.get('renderer_module',folder))
   movie=mod.Movie(card_duration_s=sec.get('chapter_card_s',2)) if index==5 else mod.Movie()
   movie.voices=[]
   lines=mod.CAPTIONS
   if index==6:lines=sec.get('caption_lines',[['実機への展開を見据え、実在する小型ドローンとカメラ、','制御用パソコンを組み合わせた構成にしています。']]+lines[1:])
   def frame(t):
    picture_t=t
    if index==1:
     # Keep each explanatory animation aligned with its newly paced sentence.
     old=sec['old_voices'];new_points=[0];old_points=[0]
     for a,b in zip(voices,old):new_points += [a['start'],a['start']+a['duration_s']];old_points += [b['start'],b['start']+b['duration_s']]
     new_points += [duration];old_points += [28]
     picture_t=float(np.interp(t,new_points,old_points))
    elif index==6:picture_t=float(np.interp(t,[0,sec['hardware_end_s'],duration],[0,15,30]))
    im=movie.frame(picture_t)
    for i,v in enumerate(voices):
     if v['start']<=t<v['start']+v['duration_s']+.1:
      for j,line in enumerate(lines[i]):
       if index==1:y=979+j*51 if len(lines[i])>1 else 1006;n=36;anchor='ms'
       elif index==5:y=1000+j*38;n=28;anchor='mt'
       else:y=981+j*43 if len(lines[i])>1 else 1007;n=31;anchor='mt'
       text(im,960,y,line,n,WHITE,450,anchor=anchor)
    return im
  silent=dest/'silent.mp4';os.environ['IMAGEIO_FFMPEG_EXE']='ffmpeg'
  with imageio.get_writer(silent,fps=FPS,codec='h264_nvenc',macro_block_size=1,ffmpeg_params=['-cq','18','-preset','p5','-pix_fmt','yuv420p'],ffmpeg_log_level='error') as writer:
   for n in range(duration*FPS):
    writer.append_data(np.asarray(frame(n/FPS)))
    if n%240==0:print('FRAME',folder,n,flush=True)
  sample=voices[0]['start']+min(2,voices[0]['duration_s']/2)
  frame(sample).save(dest/'preview.png')
  if index==5 and hasattr(movie,'evidence'):
   (dest/'source_evidence.json').write_text(json.dumps(movie.evidence(),ensure_ascii=False,indent=2),encoding='utf8')
 run(['ffmpeg','-v','error','-y','-i',str(silent),'-i',str(dest/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-ar','96000','-b:a','192k','-af','loudnorm=I=-16:TP=-2:LRA=7','-t',str(duration),'-movflags','+faststart',sec['render_file']])
 print('SECTION_COMPLETE',folder,flush=True)

def assemble():
 from ending_movie import join
 sections=json.loads((OUT/'plan.json').read_text(encoding='utf8'))
 paths=[Path(s['render_file']) for s in sections];durations=[s['duration_s'] for s in sections]
 staging=OUT/'final.mp4';join(paths,durations,staging,'consistent_narration')
 run(['ffmpeg','-v','error','-xerror','-i',str(staging),'-f','null','-'])
 probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(staging)]).stdout)
 video=next(s for s in probe['streams'] if s['codec_type']=='video')
 assert int(video['nb_frames'])==sum(durations)*FPS and abs(float(probe['format']['duration'])-sum(durations))<.05
 assert not any(s['codec_type']=='subtitle' for s in probe['streams'])
 def hashes(p):
  s=run(['ffmpeg','-v','error','-i',str(p),'-map','0:v:0','-f','framemd5','-']).stdout.decode()
  return [l.split(',')[-1].strip() for l in s.splitlines() if l and not l.startswith('#')]
 # These evidence scenes must remain exactly the same pictures at the same speed.
 for index in [3,4]:assert hashes(paths[index])==hashes(sections[index]['source_video'])
 transcript=[];chapters=[];offset=0
 for s in sections:
  chapters.append(dict(section=s['folder'],start_s=offset,duration_s=s['duration_s']))
  for v in s['voices']:transcript.append(dict(start=offset+v['start'],end=offset+v['start']+v['duration_s'],text=v['text']))
  offset+=s['duration_s']
 assert all(a['end']<b['start'] for a,b in zip(transcript,transcript[1:]))
 def stamp(t):
  n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
 (OUT/'transcript_review.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(transcript)),encoding='utf8')
 # Stage a separately named delivery so the new audio cannot be confused with a cached player session.
 dest=VIDEO/os.environ.get('RESCUE_VIDEO_FILENAME','rescue_drone_final_narration_revised.mp4');staging.replace(dest)
 report=dict(video=str(dest),duration_s=sum(durations),frames=int(video['nb_frames']),dimensions=[1920,1080],fps=FPS,chapters=chapters,sha256=sha(dest),full_decode=True,blue_and_red_flight_frames_preserved=True,subtitle_delivery='Burned-in only; transcript is kept in the work folder',narration_pace='6.8 mora/s plus punctuation allowance; pitch-preserving adjustment of original voice clips',new_training_text=NEW_TEXT,voice_overlap=False,source_sections=[dict(path=str(p),sha256=sha(p)) for p in paths],visual_review_complete=False,audio_listening_review=False)
 report.update(new_training_text=[v['text'] for v in sections[2]['voices']],training_narration_pace=sections[2].get('narration_pace','Original normalized pace'))
 dest.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 (OUT/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print('CONSISTENT_NARRATION_COMPLETE',dest,sum(durations),flush=True)
def prepare_ending():prepare([6])

if __name__=='__main__':
 if sys.argv[1]=='section':render_section(int(sys.argv[2]))
 else:globals()[sys.argv[1]]()
