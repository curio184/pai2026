"""Verified fog/dust flight excerpts and a scoped four-condition result card."""
import os,sys,json,hashlib,subprocess,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import imageio.v2 as imageio
import demo_movie as base
from demo_movie import ROOT,HERE,BG,WHITE,MUTED,CYAN,GOLD,LINE,font,text,sha,smooth,Record
OUT=HERE/'conditions_movie';OUT.mkdir(exist_ok=True)
FPS=24;DURATION=27;CONDITIONS=['fog_light','fog_dense','dust']
NAMES={'clear':'通常','fog_light':'薄い霧','fog_dense':'濃い霧','dust':'粉じん'}
DEST=ROOT/'output/video/rescue_drone_visual_conditions.mp4'
INTRO=ROOT/'output/video/rescue_drone_intro_mechanism_demo.mp4'
COMBINED=ROOT/'output/video/rescue_drone_through_conditions.mp4'
STARTS=[2.2,8.2,20.4]
CAPTIONS=[['災害現場では、霧や粉じんで','視界が悪くなることもあります。'],
 ['そこで、見え方を変えた条件でも、','同じモデルで捜索できるか確かめました。'],
 ['通常を含む四つの条件で、','発見から着陸まで完了しました。']]

class Condition(base.Movie):
 def __init__(self,condition):
  super().__init__();self.condition=condition
  self.record=Record(HERE/f'runs/eval03/{condition}_blue');self.score=self.record.score
  self.render_folder=HERE/f'movie/renders/{condition}'
  self.poses=json.loads((self.render_folder/'poses.json').read_text())
  self.projection=json.loads((OUT/condition/'trail_projection.json').read_text())
  assert self.projection['trace_sha256']==sha(self.record.path/'trace.jsonl')
  self.events=json.loads((self.record.path/'events.json').read_text())
  self.land_request=next(e['t'] for e in self.events if e['event']=='land_request')
  self.packet_map={p['sim_time_capture']:p for p in self.record.packets}
  self.notification=Image.open(self.record.path/'notification.jpg').convert('RGB')
  ImageDraw.Draw(self.base).rectangle((60,30,1000,70),fill=BG)
  text(self.base,64,35,'視界が悪い環境での捜索',24,CYAN,500)
 def state(self,t):
  index=min(len(self.poses)-1,max(0,int((t-base.LEAD)*30+1e-5)))
  meta=self.poses[index];row=self.record.rows[meta['trace_index']]
  return index,row,self.packet_map.get(row.get('model_capture_time'))
 def excerpt(self,u):
  im=super().frame(base.CARD+base.LEAD+u)
  d=ImageDraw.Draw(im);d.rectangle((1200,30,1865,70),fill=BG)
  text(im,1856,35,NAMES[self.condition],26,CYAN,500,anchor='rt')
  d.rectangle((1120,155,1320,193),fill=BG)
  text(im,1312,164,'抜粋・2倍速',20,MUTED,anchor='rt')
  return im

class Movie:
 def __init__(self,card_duration_s=2):
  self.card_duration_s=card_duration_s;self.duration_s=DURATION+card_duration_s-2
  self.movies={c:Condition(c) for c in CONDITIONS}
  self.records={'clear':Record(HERE/'runs/eval03/clear_blue'),**{c:m.record for c,m in self.movies.items()}}
  self.voices=json.loads((OUT/'voice_manifest.json').read_text(encoding='utf8'))
  checkpoints={r.score['checkpoint_sha256'][0] for r in self.records.values()};assert len(checkpoints)==1
  self.checkpoint=next(iter(checkpoints));self.metadata=[]
  assert all(r.score['success'] for r in self.records.values())
 def result(self):
  im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
  text(im,96,78,'検証結果',26,CYAN,500)
  text(im,91,145,'4条件で、発見から着陸まで完了',54,WHITE,550)
  text(im,96,241,'同じモデルで検証',28,MUTED)
  xs=[760,1060,1360,1660]
  for x,s in zip(xs,['発見','接近・停止','画像の保存','着陸']):text(im,x,343,s,28,MUTED,500,anchor='mt')
  d.line((96,401,1824,401),fill=LINE,width=1)
  for i,c in enumerate(['clear']+CONDITIONS):
   r=self.records[c];score=r.score
   assert score['checks']['three_image_discovery'] and score['checks']['original_image_notification']
   assert score['physical']['grounded_disarmed_motors_off'] and score['physical']['goal_holds']['blue']['physical_hold']['duration_s']>=3
   y=444+i*103;text(im,120,y,NAMES[c],32,WHITE,500)
   for x in xs:
    d.line((x-14,y+20,x-3,y+31,x+17,y+7),fill=CYAN,width=4)
   if i<3:d.line((96,y+74,1824,y+74),fill=LINE,width=1)
  text(im,96,885,'各条件1回 ／ 1室・固定した人物配置で検証',23,MUTED)
  return im
 def frame(self,t,log=False):
  meta=dict(video_time_s=t)
  if t<self.card_duration_s:
   im=Image.new('RGB',(1920,1080),BG)
   text(im,960,510,'視界が悪い環境での捜索',64,WHITE,500,anchor='mm')
   ImageDraw.Draw(im).line((880,602,1040,602),fill=CYAN,width=2)
   im=Image.blend(Image.new('RGB',im.size),im,min(smooth(t/.3),smooth((self.card_duration_s-t)/.2)))
   meta['kind']='chapter_card'
  elif t<self.card_duration_s+18:
   part=min(2,int((t-self.card_duration_s)/6));c=CONDITIONS[part];u=t-(self.card_duration_s+6*part);m=self.movies[c]
   im=m.excerpt(u);idx,row,p=m.state(base.LEAD+u)
   meta.update(kind='flight_excerpt',condition=c,external_frame=idx,simulation_time=row['t'],camera_id=p['id'] if p else None,camera_sha256=p['image_sha256'] if p else None,action_source=row['action_source'],actions=row['model_action'][:4] if row['action_source']=='policy' else None,translation_chunk_index=row.get('chunk_index'),yaw_chunk_index=row.get('yaw_chunk_index'))
   # Same input/action layout; reserve the bottom strip for the spoken caption.
   ImageDraw.Draw(im).rectangle((0,990,1920,1080),fill=BG)
  else:im=self.result();meta['kind']='results'
  for i,v in enumerate(self.voices):
   if v['start']<=t<v['start']+v['duration_s']+.1:
    for j,line in enumerate(CAPTIONS[i]):text(im,960,1000+j*38,line,28,WHITE,450,anchor='mt')
  if t>self.duration_s-.5:im=Image.blend(im,Image.new('RGB',im.size),smooth((t-self.duration_s+.5)/.5))
  if log:self.metadata.append(meta)
  return im

def audio():
 import make_rescue_presentation_audio as original
 generated=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'));clips=[]
 for i,(g,at) in enumerate(zip(generated,STARTS)):
  assert g['transcript_matches'] and ''.join(CAPTIONS[i])==g['text']
  assert sha(OUT/g['file'])==g['sha256']
  clips.append(dict(index=i,start=at,max_s=g['duration_s']+.1,text=g['text'],caption=g['text'],file=g['file']))
 assert all(a['start']+a['max_s']<b['start'] for a,b in zip(clips,clips[1:]))
 assert clips[-1]['start']+clips[-1]['max_s']<DURATION-.5
 (OUT/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
 original.TMP=OUT;original.PLAN=dict(duration_s=DURATION,flights=[],timeline=[dict(start=0)]);original.mix()
 review=json.loads((OUT/'audio_review.json').read_text());review.update(voice='OpenAI gpt-realtime-2.1-mini / marin',rotor='None',time_stretch_used=False)
 (OUT/'audio_review.json').write_text(json.dumps(review,indent=2))
 with wave.open(str(OUT/'dry_narration.wav'),'wb') as dst:
  dst.setnchannels(1);dst.setsampwidth(2);dst.setframerate(24000)
  for i in range(3):
   with wave.open(str(OUT/f'voice_{i:02}.wav'),'rb') as src:dst.writeframes(src.readframes(src.getnframes()))
   dst.writeframes(bytes(24000))

def preview():
 m=Movie();sheet=Image.new('RGB',(1280,1170),BG)
 for i,t in enumerate([1,5,11,17,21,24]):
  im=m.frame(t);im.save(OUT/f'preview_{i:02}.png');x=i%2*640;y=i//2*390
  text(sheet,x+10,y+4,f'{t:.1f} s',19);sheet.paste(im.resize((640,360)),(x,y+30))
 sheet.save(OUT/'preview_sheet.jpg',quality=95)

def render():
 m=Movie();os.environ['IMAGEIO_FFMPEG_EXE']='ffmpeg'
 with imageio.get_writer(OUT/'silent.mp4',fps=FPS,codec='h264_nvenc',macro_block_size=1,ffmpeg_params=['-cq','18','-preset','p5','-pix_fmt','yuv420p'],ffmpeg_log_level='error') as w:
  for i in range(DURATION*FPS):
   w.append_data(np.asarray(m.frame(i/FPS,log=True)))
   if i%120==0:print('CONDITIONS_FRAME',i,flush=True)
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','96000','-af','loudnorm=I=-16:TP=-2:LRA=7','-movflags','+faststart','-t',str(DURATION),str(DEST)],check=True)
 intro_hash=sha(INTRO);listing=OUT/'join.ffconcat'
 listing.write_text('ffconcat version 1.0\n'+''.join("file '"+str(p.resolve()).replace('\\','/')+"'\n" for p in [INTRO,DEST]),encoding='utf8')
 # Decode and trim audio before joining to remove AAC encoder padding at the seam.
 # Video frames are still stream-copied, preserving the accepted 90-second picture.
 filters=f'[1:a]atrim=duration=90,asetpts=PTS-STARTPTS[a0];[2:a]atrim=duration={DURATION},asetpts=PTS-STARTPTS[a1];[a0][a1]concat=n=2:v=0:a=1[a]'
 subprocess.run(['ffmpeg','-v','warning','-y','-f','concat','-safe','0','-i',str(listing),'-i',str(INTRO),'-i',str(DEST),'-filter_complex',filters,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-ar','96000','-movflags','+faststart','-t',str(90+DURATION),str(COMBINED)],check=True)
 assert sha(INTRO)==intro_hash
 (OUT/'frames.json').write_text(json.dumps(m.metadata,separators=(',',':')))
 evidence=dict(duration_s=DURATION,fps=FPS,accepted_intro_sha256=intro_hash,conditions=CONDITIONS,checkpoint_sha256=m.checkpoint,excerpts_s=6,playback_speed=2,all_four_conditions_success=True,trials_per_condition=1,input_images='Original JPEGs without added fog, denoising or enhancement',external_source='Existing render of each recorded flight in the tested optical environment',scope='One room; fixed people; optical density not physically calibrated',records={c:dict(score_sha256=sha(r.path/'search_score.json'),trace_sha256=sha(r.path/'trace.jsonl')) for c,r in m.records.items()})
 (OUT/'source_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
 print('CONDITIONS_COMPLETE',COMBINED,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
