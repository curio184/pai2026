"""Development contribution slide; static preview, not the runtime data flow."""
import os,json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT'])
OUT=ROOT/'output/video/mechanism_review'
BG='#091319';WHITE='#eef1ee';MUTED='#a9b8be';CYAN='#7ccac6';GOLD='#dfbf8a';LINE='#31444d'
im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im);boxes=[]
def font(n,w=450):
 f=ImageFont.truetype('C:/Windows/Fonts/NotoSansJP-VF.ttf',n);f.set_variation_by_axes([w]);return f
def text(x,y,s,n=28,c=WHITE,w=450,anchor='lt'):
 f=font(n,w);b=d.textbbox((x,y),s,font=f,anchor=anchor)
 assert b[0]>=80 and b[2]<=1840 and b[1]>=0 and b[3]<1030,(s,b)
 d.text((x,y),s,font=f,fill=c,anchor=anchor);boxes.append(dict(text=s,bounds=b,size=n))
def arrow(a,b,c=CYAN,width=3,head=11):
 d.line((*a,*b),fill=c,width=width)
 dx=b[0]-a[0];dy=b[1]-a[1];l=math.hypot(dx,dy);ux=dx/l;uy=dy/l
 d.polygon([b,(b[0]-head*ux+head*.55*uy,b[1]-head*uy-head*.55*ux),(b[0]-head*ux-head*.55*uy,b[1]-head*uy+head*.55*ux)],fill=c)

text(96,108,'SmolVLAの追加学習',57,WHITE,560)

# Two development steps, rather than another input/model/output architecture.
text(96,296,'01',27,CYAN,500)
text(161,292,'飛行動作を定義',40,WHITE,500)
text(161,354,'何を出力させるかを決める',26,MUTED)
centers=[820,1210,1600]
cx,cy=centers[0],346
arrow((cx-42,cy),(cx+42,cy));arrow((cx+42,cy),(cx-42,cy))
arrow((cx,cy-42),(cx,cy+42));arrow((cx,cy+42),(cx,cy-42))
cx=centers[1]
d.arc((cx-40,cy-40,cx+40,cy+40),35,318,fill=CYAN,width=3)
ang=math.radians(318);end=(cx+40*math.cos(ang),cy+40*math.sin(ang))
v=(-math.sin(ang),math.cos(ang))
arrow((end[0]-v[0]*13,end[1]-v[1]*13),end)
cx=centers[2]
arrow((cx-22,cy+26),(cx-22,cy-33));arrow((cx+22,cy-33),(cx+22,cy+26))
d.line((cx-48,cy+41,cx+48,cy+41),fill=CYAN,width=3)
for x,s in zip(centers,['移動速度','旋回速度','離陸・着陸の要求']):text(x,426,s,31,WHITE,500,'mt')
text(820,479,'前後・左右・上下',25,MUTED,450,'mt')

d.line((96,563,1824,563),fill=LINE,width=1)
text(96,631,'02',27,GOLD,500)
text(161,627,'飛行データで',40,WHITE,500)
text(161,684,'追加学習',40,WHITE,500)
text(161,756,'映像や指示から動作を学ぶ',26,MUTED)

text(1210,627,'シミュレーターで教師データを作成',29,MUTED,450,'mt')
left=(630,706,1148,834);right=(1272,706,1790,834)
for rect in [left,right]:d.rectangle(rect,fill='#0e1b23',outline=LINE,width=1)
text(889,752,'映像・指示・機体の状態',30,WHITE,500,'mt')
text(1531,752,'対応する飛行動作',30,WHITE,500,'mt')
d.line((1149,771,1271,771),fill=GOLD,width=2)
text(1210,734,'組',23,GOLD,500,'mt')
# Both halves of each training example feed the same fine-tuning operation.
d.line((889,835,889,881,1531,881,1531,835),fill=GOLD,width=2)
arrow((1210,881),(1210,913),GOLD,2,9)
text(1210,943,'SmolVLAを追加学習',35,GOLD,500,'mt')

OUT.mkdir(exist_ok=True,parents=True)
im.save(OUT/'smolvla_training_overview.png')
(OUT/'smolvla_training_overview.json').write_text(json.dumps(dict(status='Static review slide only; video unchanged',message='SmolVLAにドローンの飛行動作を学習させる',dimensions=[1920,1080],text=boxes,sources=['smolvla_policy.py','outputs/smolvla_training_realism_precision_02/started.json','outputs/smolvla_training_realism_precision_02/result.json','outputs/vla_data_realism_precision_02/manifest.json'],notes=['This illustrates development steps and supervised data pairing, not the live control loop.','No action-expert architecture replacement or full-model training claim.','Takeoff and landing outputs are request scores handled by control software.']),ensure_ascii=False,indent=2),encoding='utf8')
print(OUT/'smolvla_training_overview.png')
