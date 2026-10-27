"""Same model, new red-person mission: recorded input/action display and video edit."""
import os,sys,json,hashlib,subprocess,shutil,wave,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import imageio.v2 as imageio
import demo_movie as base
from demo_movie import ROOT,HERE,BG,WHITE,MUTED,CYAN,GOLD,LINE,font,text,sha,smooth,Record
OUT=HERE/'red_movie';PLAN=json.loads((OUT/'plan.json').read_text());FPS=24;DURATION=PLAN['duration_s'];LEAD=PLAN['lead_s']
DEST=ROOT/'output/video/rescue_drone_red_search.mp4'
INTRO=ROOT/'output/video/rescue_drone_intro_mechanism_demo.mp4'
CONDITIONS=ROOT/'output/video/rescue_drone_visual_conditions.mp4'
COMBINED=ROOT/'output/video/rescue_drone_with_red_search.mp4'

class Movie(base.Movie):
 def __init__(self):
  super().__init__();self.record=Record(Path(PLAN['record']));self.score=self.record.score
  assert self.score['success']
  assert self.score['checkpoint_sha256']==json.loads((HERE/'runs/eval03/clear_blue/search_score.json').read_text())['checkpoint_sha256']
  self.render_folder=OUT/'renders';self.poses=json.loads((self.render_folder/'poses.json').read_text())
  self.projection=json.loads((OUT/'trail_projection.json').read_text());assert self.projection['trace_sha256']==sha(self.record.path/'trace.jsonl')
  self.events=json.loads((self.record.path/'events.json').read_text());self.land_request=next(e['t'] for e in self.events if e['event']=='land_request')
  self.packet_map={p['sim_time_capture']:p for p in self.record.packets}
  self.notification=Image.open(self.record.path/'notification.jpg').convert('RGB');self.target_label='赤い服の人物を確認'
  d=ImageDraw.Draw(self.base);d.rectangle((60,30,1220,143),fill=BG)
  text(self.base,64,35,'指示を変えて捜索',24,CYAN,500)
  text(self.base,60,83,'「赤い服の人を探して」',46,WHITE,550)
  self.metadata=[]
 def state(self,t):
  idx=min(len(self.poses)-1,max(0,int(max(0,t-base.LEAD)*FPS+1e-6)))
  meta=self.poses[idx];row=self.record.rows[meta['trace_index']]
  return idx,row,self.packet_map.get(row.get('model_capture_time'))
 def frame(self,t,log=False):
  virtual=base.CARD+base.LEAD+t-LEAD
  im=super().frame(virtual,log=False)
  idx,row,p=self.state(base.LEAD+t-LEAD)
  started=t>=LEAD;done=started and row['t']>=self.score['completion_time_s']-1e-6
  d=ImageDraw.Draw(im);d.rectangle((990,153,1320,193),fill=BG)
  text(im,1312,164,'抜粋・2倍速' if started and not done else '捜索開始前' if not started else '飛行終了',20,MUTED,anchor='rt')
  # The new clip starts after takeoff; make the opening prompt lead-in explicit.
  if not started:
   d.rectangle((1360,878,1860,914),fill=BG);text(im,1360,886,'同じモデルに、別の人物を指示',19,MUTED)
  if log:
   active=started and not done and row['t']<self.land_request and row['action_source']=='policy'
   self.metadata.append(dict(video_time_s=t,external_frame=idx,simulation_time=row['t'],phase=row['phase'],camera_id=p['id'] if p else None,camera_sha256=p['image_sha256'] if p else None,action_source=row['action_source'],actions=row['model_action'][:4] if active else None,translation_chunk_index=row.get('chunk_index') if active else None,yaw_chunk_index=row.get('yaw_chunk_index') if active else None,landing_autopilot=row['t']>=self.land_request and not done,completed=done))
  if t<.4:im=Image.blend(Image.new('RGB',im.size),im,smooth(t/.4))
  if t>DURATION-.5:im=Image.blend(im,Image.new('RGB',im.size),smooth((t-DURATION+.5)/.5))
  return im

def audio():
 import make_rescue_presentation_audio as original
 g=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'))[0]
 assert g['transcript_matches'] and sha(OUT/'voice_00.wav')==g['sha256']
 clips=[dict(index=0,start=.6,max_s=2.5,text=g['text'],caption=g['text'],file='voice_00.wav')]
 (OUT/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
 original.TMP=OUT;original.PLAN=dict(duration_s=DURATION,flights=[],timeline=[dict(start=0)]);original.mix()
 review=json.loads((OUT/'audio_review.json').read_text());review.update(voice='OpenAI gpt-realtime-2.1-mini / marin',rotor='None',time_stretch_used=False)
 (OUT/'audio_review.json').write_text(json.dumps(review,indent=2));shutil.copy2(OUT/'voice_00.wav',OUT/'dry_narration.wav')

def preview():
 m=Movie();sheet=Image.new('RGB',(1280,780),BG)
 for j,idx in enumerate([0,len(m.poses)//3,2*len(m.poses)//3,len(m.poses)-1]):
  t=LEAD+idx/FPS;im=m.frame(t);im.save(OUT/f'preview_{j:02}.png');x=j%2*640;y=j//2*390
  text(sheet,x+10,y+4,f'{t:.1f} s',19);sheet.paste(im.resize((640,360)),(x,y+30))
 sheet.save(OUT/'preview_sheet.jpg',quality=95)

def render():
 m=Movie()
 os.environ['IMAGEIO_FFMPEG_EXE']='ffmpeg'
 with imageio.get_writer(OUT/'silent.mp4',fps=FPS,codec='h264_nvenc',macro_block_size=1,ffmpeg_params=['-cq','18','-preset','p5','-pix_fmt','yuv420p'],ffmpeg_log_level='error') as w:
  for i in range(DURATION*FPS):
   idx,_,_=m.state(base.LEAD+i/FPS-LEAD);file=OUT/'renders'/f'{idx:04d}.jpg'
   deadline=time.monotonic()+120
   while not file.exists() or time.time()-file.stat().st_mtime<.3:
    if time.monotonic()>deadline:raise TimeoutError('Waiting for recorded-pose rendering: '+str(file))
    time.sleep(.2)
   w.append_data(np.asarray(m.frame(i/FPS,log=True)))
   if i%120==0:print('RED_COMPOSITE_FRAME',i,flush=True)
 assert len(list((OUT/'renders').glob('*.jpg')))==PLAN['render_frames']
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','96000','-af','loudnorm=I=-16:TP=-2:LRA=7','-movflags','+faststart','-t',str(DURATION),str(DEST)],check=True)
 before={str(p):sha(p) for p in [INTRO,CONDITIONS]};listing=OUT/'join.ffconcat'
 listing.write_text('ffconcat version 1.0\n'+''.join("file '"+str(p.resolve()).replace('\\','/')+"'\n" for p in [INTRO,DEST,CONDITIONS]),encoding='utf8')
 filters=f'[1:a]atrim=duration=90,asetpts=PTS-STARTPTS[a0];[2:a]atrim=duration={DURATION},asetpts=PTS-STARTPTS[a1];[3:a]atrim=duration=27,asetpts=PTS-STARTPTS[a2];[a0][a1][a2]concat=n=3:v=0:a=1[a]'
 subprocess.run(['ffmpeg','-v','warning','-y','-f','concat','-safe','0','-i',str(listing),'-i',str(INTRO),'-i',str(DEST),'-i',str(CONDITIONS),'-filter_complex',filters,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-ar','96000','-movflags','+faststart','-t',str(117+DURATION),str(COMBINED)],check=True)
 assert all(sha(Path(p))==v for p,v in before.items())
 (OUT/'frames.json').write_text(json.dumps(m.metadata,separators=(',',':')))
 evidence=dict(duration_s=DURATION,fps=FPS,playback_speed=2,lead_s=LEAD,record=str(m.record.path),accepted_files_sha256=before,trace_sha256=sha(m.record.path/'trace.jsonl'),search_score_sha256=sha(m.record.path/'search_score.json'),checkpoint_sha256=m.score['checkpoint_sha256'][0],same_checkpoint_as_blue=True,additional_training=False,new_flight=True,attempt='eval_red01',target='red',success=True,red_hold_s=m.score['physical']['goal_holds']['red']['physical_hold']['duration_s'],input_images='Original recorded JPEGs without enhancement',external_render_source=str(OUT/'render_source.json'),scope='One room; stationary people; simulation; no hardware test',sequence=['approved_intro_and_blue_demo','red_search','approved_visual_conditions'])
 (OUT/'source_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
 print('RED_MOVIE_COMPLETE',COMBINED,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
