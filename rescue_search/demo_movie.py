"""Approved demo layout, recorded camera/action synchronization, and projected history."""
import os,sys,json,hashlib,math,shutil,subprocess
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import imageio.v2 as imageio
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);sys.path.insert(0,str(ROOT))
HERE=Path(__file__).resolve().parent;OUT=HERE/'demo_movie';OUT.mkdir(exist_ok=True)
from edit_movie import Record
BG='#091319';WHITE='#eef1ee';MUTED='#a9b8be';CYAN='#7ccac6';GOLD='#dfbf8a';LINE='#2b3c43'
FPS=24;CARD=4.;DURATION=40;LEAD=4.;SPEED=2.
DEST=ROOT/'output/video/rescue_drone_demonstration.mp4'
INTRO=ROOT/'output/video/rescue_drone_intro_and_mechanism.mp4'
COMBINED=ROOT/'output/video/rescue_drone_intro_mechanism_demo.mp4'
PHASE={'takeoff':'離陸','hover':'その場で待機','right':'室内を見渡す','confirm':'人物を確認','blue':'対象者に接近','red':'対象者に接近','report':'停止して確認','land':'着陸を準備','reacquire':'対象者を再確認'}
@lru_cache(None)
def font(n,w=450):
 f=ImageFont.truetype('C:/Windows/Fonts/NotoSansJP-VF.ttf',n);f.set_variation_by_axes([w]);return f
def text(im,x,y,s,n=26,c=WHITE,w=450,anchor='lt'):
 ImageDraw.Draw(im).text((x,y),s,font=font(n,w),fill=c,anchor=anchor)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)

class Movie:
 def __init__(self):
  self.record=Record(HERE/'runs/eval03/clear_blue');self.score=self.record.score
  self.poses=json.loads((HERE/'movie/renders/demo/poses.json').read_text())
  self.render_folder=HERE/'movie/renders/demo'
  self.projection=json.loads((OUT/'trail_projection.json').read_text())
  assert self.projection['trace_sha256']==sha(self.record.path/'trace.jsonl')
  self.events=json.loads((self.record.path/'events.json').read_text())
  self.land_request=next(e['t'] for e in self.events if e['event']=='land_request')
  self.packet_map={p['sim_time_capture']:p for p in self.record.packets}
  self.notification=Image.open(self.record.path/'notification.jpg').convert('RGB')
  self.target_label='青い服の人物を確認'
  self.base=Image.new('RGB',(1920,1080),BG)
  text(self.base,64,35,'捜索の実演',24,CYAN,500)
  text(self.base,60,83,'「青い服の人を探して」',46,WHITE,550)
  text(self.base,64,158,'外部カメラ',25,MUTED)
  text(self.base,1360,158,'VLAへの入力画像',25,CYAN,500)
  text(self.base,1368,575,'実際にモデルへ渡した画像',21,MUTED)
  ImageDraw.Draw(self.base).line((1360,623,1856,623),fill=LINE,width=1)
  self.metadata=[]

 def state(self,t):
  frame=min(959,max(0,int(max(0,t-LEAD)*SPEED*15+1e-6)))
  meta=self.poses[frame];row=self.record.rows[meta['trace_index']]
  packet=self.packet_map.get(row.get('model_capture_time'))
  return frame,row,packet

 def frame(self,t,log=False):
  video_time=t
  if t<CARD:
   im=Image.new('RGB',(1920,1080),BG)
   text(im,960,481,'シミュレーターでの実演',72,WHITE,500,anchor='mm')
   text(im,960,603,'MuJoCo',46,CYAN,500,anchor='mm')
   ImageDraw.Draw(im).line((880,681,1040,681),fill=CYAN,width=2)
   alpha=min(smooth(t/.3),smooth((CARD-t)/.2))
   im=Image.blend(Image.new('RGB',im.size),im,alpha)
   if log:self.metadata.append(dict(video_time_s=t,kind='chapter_card',narration=False))
   return im
  t-=CARD
  index,row,packet=self.state(t);moment=row['t'];started=t>=LEAD
  done=started and moment>=self.score['completion_time_s']-1e-6
  landing=started and moment>=self.land_request and not done
  active=started and not landing and not done and row['action_source']=='policy'
  a=row['model_action'];im=self.base.copy();d=ImageDraw.Draw(im)
  status='指示を送信' if not started else 'ミッション完了' if done else '着陸中' if landing else PHASE[row['phase']]
  text(im,1856,87,status,30,CYAN if done else GOLD,500,anchor='rt')
  text(im,1312,164,'2倍速' if started and not done else '飛行開始前' if not started else '飛行終了',20,MUTED,anchor='rt')
  exterior=Image.open(self.render_folder/f'{index:04d}.jpg').convert('RGBA')
  overlay=Image.new('RGBA',exterior.size);od=ImageDraw.Draw(overlay)
  projected=self.projection['frames'][index];points=projected['past_points']
  if started and moment>18 and not done:
   for j,(p,q) in enumerate(zip(points,points[1:])):
    if p[2]>0 and q[2]>0 and math.dist(p[:2],q[:2])>0.1:
     od.line((*p[:2],*q[:2]),fill=(124,202,198,round(35+115*j/40)),width=3)
   if row['phase']=='right':
    p,q=projected['center'],projected['front'];dx=q[0]-p[0];dy=q[1]-p[1];dist=math.hypot(dx,dy)
    if dist>8:
     od.line((*p[:2],*q[:2]),fill=(223,191,138,195),width=3)
     vx,vy=dx/dist,dy/dist
     od.polygon([tuple(q[:2]),(q[0]-11*vx+5*vy,q[1]-11*vy-5*vx),(q[0]-11*vx-5*vy,q[1]-11*vy+5*vx)],fill=(223,191,138,195))
  exterior=Image.alpha_composite(exterior,overlay).convert('RGB')
  im.paste(exterior.resize((1248,780),Image.Resampling.LANCZOS),(64,198))
  if packet:
   onboard=self.record.inputs[packet['id']]
   im.paste(onboard.resize((480,360),Image.Resampling.NEAREST),(1368,198))
   age=moment-packet['sim_time_capture']
   text(im,1368,603,('最後に受け取った画像' if done else f'映像取得から {age:.2f} 秒'),16,MUTED)
  else:text(im,1410,360,'画像の受信待ち',25,MUTED)
  text(im,1360,645,'VLAが生成した動作',25,GOLD,500)
  state_label='実行中' if active else '指示待ち' if not started else '飛行終了' if done else '着陸制御中' if landing else '更新待ち'
  text(im,1856,650,state_label,20,MUTED,anchor='rt')
  names=[('前進','後退'),('左移動','右移動'),('上昇','下降'),('右旋回','左旋回')]
  for k in range(4):
   y=698+k*43;label=names[k][0 if a[k]>=0 else 1] if active else ['前後','左右','上下','旋回'][k]
   text(im,1360,y,label,23)
   x0,x1=1485,1651;mid=(x0+x1)/2;cy=y+15
   d.line((x0,cy,x1,cy),fill=LINE,width=5);d.line((mid,cy-7,mid,cy+7),fill='#596a71',width=1)
   if active:
    scale=[.2,.2,.3,.35][k];end=mid+max(-1,min(1,a[k]/scale))*(x1-mid)
    d.line((min(mid,end),cy,max(mid,end),cy),fill=GOLD,width=5);d.ellipse((end-3,cy-3,end+3,cy+3),fill=GOLD)
    number=f'{abs(a[k]):.3f} m/s' if k<3 else f'{abs(math.degrees(a[k])):.2f} °/s'
   else:number='—'
   text(im,1856,y,number,23,WHITE,anchor='rt')
  text(im,1360,886,'生成した動作列' if active else '着陸指示を送信済み' if landing else '指示に合わせて動作を更新' if started and not done else '飛行を終了しました' if done else '指示を受けて飛行を開始',19,MUTED)
  for j,(label,idx) in enumerate([('移動',row.get('chunk_index')),('旋回',row.get('yaw_chunk_index'))]):
   y=920+j*29;text(im,1360,y,label,18,MUTED)
   for k in range(32):
    x=1420+k*11.4;color=GOLD if active and k==idx else '#52666c' if active and idx is not None and k<idx else '#23353e'
    d.rectangle((x,y+4,x+7,y+16),fill=color)
   text(im,1856,y,f'{idx+1}/32' if active and idx is not None else '—',18,GOLD,anchor='rt')
  # A toast confirms the saved original observation without replacing the VLA input.
  notice=self.score['notification_time_s'];found=self.score['discovery_time_s']
  if started and notice<=moment<notice+6:
   layer=Image.new('RGBA',im.size);ld=ImageDraw.Draw(layer)
   ld.rectangle((88,856,794,952),fill=(9,19,25,235));im=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
   im.paste(self.notification.resize((96,72),Image.Resampling.NEAREST),(100,868))
   text(im,216,870,'確認画像を保存しました',28,CYAN,500)
   text(im,216,912,self.target_label,21,MUTED)
  d=ImageDraw.Draw(im)
  labels=['捜索','人物を発見','接近・停止','確認画像を保存','着陸'];xs=[138,453,802,1162,1630]
  current=4 if moment>=notice else 3 if row['phase']=='report' else 2 if moment>=found else 0
  d.line((148,1032,1630,1032),fill=LINE,width=2)
  for i,(label,x) in enumerate(zip(labels,xs)):
   complete=done or started and i<current;sel=started and not done and i==current
   col=CYAN if complete else GOLD if sel else '#63767e'
   d.ellipse((x-6,1026,x+6,1038),fill=col);width=font(24,500 if sel else 450).getlength(label)
   d.rectangle((x+17,1014,x+29+width,1054),fill=BG);text(im,x+23,1018,label,24,col,500 if sel else 450)
  if not started:
   d.line((78,143,78+min(550,550*max(0,t-.8)/2.2),143),fill=CYAN,width=2)
  if log:
   self.metadata.append(dict(video_time_s=video_time,external_frame=index,simulation_time=moment,phase=row['phase'],camera_id=packet['id'] if packet else None,camera_sha256=packet['image_sha256'] if packet else None,camera_capture_time=packet['sim_time_capture'] if packet else None,action_source=row['action_source'],actions_displayed=a[:4] if active else None,translation_chunk_index=row.get('chunk_index') if active else None,yaw_chunk_index=row.get('yaw_chunk_index') if active else None,landing_autopilot=landing,completed=done))
  if t<.4:im=Image.blend(Image.new('RGB',im.size),im,smooth(t/.4))
  if video_time>DURATION-.5:im=Image.blend(im,Image.new('RGB',im.size),smooth((video_time-(DURATION-.5))/.5))
  return im

def audio():
 import make_rescue_presentation_audio as original
 source=HERE/'intro_openai';meta=json.loads((source/'voice_01.json').read_text(encoding='utf8'))
 assert meta['transcript_matches'] and meta['text']=='青い服の人を探して。'
 assert sha(source/'voice_01.wav')==meta['sha256']
 shutil.copy2(source/'voice_01.wav',OUT/'voice_00.wav')
 clips=[dict(index=0,start=CARD+.8,max_s=2.5,text=meta['text'],caption=meta['text'],file='voice_00.wav')]
 (OUT/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
 original.TMP=OUT;original.PLAN=dict(duration_s=DURATION,flights=[],timeline=[dict(start=0)]);original.mix()
 review=json.loads((OUT/'audio_review.json').read_text());review.update(voice='OpenAI gpt-realtime-2.1-mini / marin; reused approved command',rotor='None',voice_source_sha256=meta['sha256'],time_stretch_used=False)
 (OUT/'audio_review.json').write_text(json.dumps(review,indent=2))

def preview():
 m=Movie();times=[1,4,10,17,24,31,34,36];sheet=Image.new('RGB',(1280,1560),BG)
 for i,t in enumerate(times):
  im=m.frame(t);im.save(OUT/f'preview_{i:02}.png');x=i%2*640;y=i//2*390
  text(sheet,x+10,y+4,f'{t:.1f} s',19);sheet.paste(im.resize((640,360)),(x,y+30))
 sheet.save(OUT/'preview_sheet.jpg',quality=95)

def render():
 m=Movie();os.environ['IMAGEIO_FFMPEG_EXE']='ffmpeg'
 with imageio.get_writer(OUT/'silent.mp4',fps=FPS,codec='h264_nvenc',macro_block_size=1,ffmpeg_params=['-cq','18','-preset','p5','-pix_fmt','yuv420p'],ffmpeg_log_level='error') as w:
  for i in range(DURATION*FPS):
   w.append_data(np.asarray(m.frame(i/FPS,log=True)))
   if i%120==0:print('DEMO_FRAME',i,flush=True)
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','96000','-af','loudnorm=I=-16:TP=-2:LRA=7','-movflags','+faststart','-t',str(DURATION),str(DEST)],check=True)
 intro_hash=sha(INTRO);listing=OUT/'join.ffconcat'
 listing.write_text('ffconcat version 1.0\n'+''.join("file '"+str(p.resolve()).replace('\\','/')+"'\n" for p in [INTRO,DEST]),encoding='utf8')
 subprocess.run(['ffmpeg','-v','warning','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(COMBINED)],check=True)
 assert sha(INTRO)==intro_hash
 (OUT/'frames.json').write_text(json.dumps(m.metadata,separators=(',',':')))
 evidence=dict(duration_s=DURATION,fps=FPS,chapter_card_s=CARD,chapter_card_music_only=True,playback_speed=SPEED,lead_s=LEAD,accepted_intro_sha256=intro_hash,trace_sha256=sha(m.record.path/'trace.jsonl'),input_images='Original recorded JPEGs, nearest-neighbour enlargement only',trail='Four seconds of recorded past positions projected through the original camera',external_source=str(HERE/'movie/renders/demo'),land_request_time=m.land_request,action_display='Recorded applied translation and yaw steps; disabled during handoff and landing autopilot',audio_source=str(HERE/'intro_openai/voice_01.json'),no_hardware_flight_claim=True)
 (OUT/'source_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
 print('DEMO_COMPLETE',COMBINED,flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
