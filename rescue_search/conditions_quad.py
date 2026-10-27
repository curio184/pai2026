"""Four recorded model-input views, aligned around successful image notification."""
import json,bisect
from PIL import Image,ImageDraw
from demo_movie import HERE,BG,WHITE,MUTED,CYAN,GOLD,LINE,text,smooth,Record,sha
NAMES={'clear':'通常','fog_light':'薄い霧','fog_dense':'濃い霧','dust':'粉じん'}
CAPTIONS=[['災害現場を想定し、霧や粉じんで視界が悪くなる条件でも、','捜索できることを確かめました。']]
class Movie:
 def __init__(self,card_duration_s=4):
  self.voices=[];self.records={c:Record(HERE/f'runs/eval03/{c}_blue') for c in NAMES}
  assert all(r.score['success'] and r.score['checks']['original_image_notification'] for r in self.records.values())
  assert len({r.score['checkpoint_sha256'][0] for r in self.records.values()})==1
  self.used={c:set() for c in NAMES}
  self.windows={c:dict(start_s=r.score['notification_time_s']-17,end_s=r.score['notification_time_s']+1,found_s=r.score['discovery_time_s'],saved_s=r.score['notification_time_s']) for c,r in self.records.items()}
 def card(self,t):
  im=Image.new('RGB',(1920,1080),BG)
  text(im,960,510,'視界が悪い環境での捜索',64,WHITE,500,anchor='mm')
  ImageDraw.Draw(im).line((880,602,1040,602),fill=CYAN,width=2)
  return Image.blend(Image.new('RGB',im.size),im,min(smooth(t/.3),smooth((4-t)/.2)))
 def grid(self,u):
  im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
  text(im,96,34,'視界が悪い環境での捜索',28,WHITE,500)
  text(im,1824,39,'VLAへの入力画像',24,CYAN,500,anchor='rt')
  text(im,1824,77,'実際の入力画像 ／ 成功場面の抜粋・2倍速',18,MUTED,anchor='rt')
  # Preserve full 4:3 images and their original pixel detail; no enhancement or overlays on image pixels.
  for k,(c,r) in enumerate(self.records.items()):
   x=352+(k%2)*688;y=140+(k//2)*440
   w=self.windows[c];moment=w['start_s']+min(u,9)*2
   _,row,packet,observation=r.at(moment)
   assert packet is not None and observation is not None,(c,moment)
   self.used[c].add(packet['id'])
   assert observation.width*3==observation.height*4,observation.size
   im.paste(observation.resize((528,396),Image.Resampling.NEAREST),(x,y))
   text(im,x,y-39,NAMES[c],29,WHITE,500)
   saved=moment>=w['saved_s'];found=moment>=w['found_s']
   status='確認画像を保存' if saved else '対象者を発見' if found else '捜索中'
   text(im,x+528,y-34,status,23,CYAN if saved else GOLD,500,anchor='rt')
  return im
 def result(self):
  im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
  text(im,96,78,'検証結果',26,CYAN,500)
  text(im,91,145,'4条件で、発見から着陸まで完了',54,WHITE,550)
  text(im,96,241,'同じモデルで検証',28,MUTED)
  xs=[760,1060,1360,1660]
  for x,s in zip(xs,['発見','接近・停止','画像の保存','着陸']):text(im,x,343,s,28,MUTED,500,anchor='mt')
  d.line((96,401,1824,401),fill=LINE,width=1)
  for i,(c,r) in enumerate(self.records.items()):
   assert r.score['physical']['grounded_disarmed_motors_off']
   y=444+i*103;text(im,120,y,NAMES[c],32,WHITE,500)
   for x in xs:d.line((x-14,y+20,x-3,y+31,x+17,y+7),fill=CYAN,width=4)
   if i<3:d.line((96,y+74,1824,y+74),fill=LINE,width=1)
  text(im,96,885,'各条件1回 ／ 1室・固定した人物配置で検証',23,MUTED)
  return im
 def frame(self,t):
  if t<4:return self.card(t)
  im=self.grid(t-4) if t<14 else self.result()
  if t>17.5:im=Image.blend(im,Image.new('RGB',im.size),smooth((t-17.5)/.5))
  return im
 def evidence(self):
  return dict(source='Original recorded VLA input JPEGs; hash verified by Record',no_image_enhancement=True,resize='nearest neighbour',independent_flights=True,aligned_event='notification/image saved',playback_speed=2,terminal_hold_s=1,windows=self.windows,records={c:dict(score_sha256=sha(r.path/'search_score.json'),trace_sha256=sha(r.path/'trace.jsonl'),packet_ids=sorted(self.used[c])) for c,r in self.records.items()})

if __name__=='__main__':
 out=HERE/'narration_consistent/conditions_quad';out.mkdir(exist_ok=True)
 m=Movie()
 for t in [5,10,13.5]:m.frame(t).save(out/f'layout_{t}.png')
 print(json.dumps(m.evidence(),ensure_ascii=False),flush=True)
