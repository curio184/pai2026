"""Static review slide: implementation-backed SmolVLA adaptation overview."""
import os,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT'])
OUT=ROOT/'output/video/mechanism_review'
BG='#091319';WHITE='#eef1ee';MUTED='#a9b8be';CYAN='#7ccac6';GOLD='#dfbf8a';LINE='#31444d'
im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
boxes=[]
def font(n,w=450):
 f=ImageFont.truetype('C:/Windows/Fonts/NotoSansJP-VF.ttf',n);f.set_variation_by_axes([w]);return f
def text(x,y,s,n=28,c=WHITE,w=450,anchor='lt'):
 f=font(n,w);box=d.textbbox((x,y),s,font=f,anchor=anchor)
 assert box[0]>=60 and box[2]<=1860 and box[1]>=0 and box[3]<1050,(s,box)
 d.text((x,y),s,font=f,fill=c,anchor=anchor)
 boxes.append(dict(text=s,bounds=box,size=n))
def arrow(x1,x2,y,c):
 d.line((x1,y,x2-12,y),fill=c,width=3)
 d.polygon([(x2,y),(x2-14,y-7),(x2-14,y+7)],fill=c)

text(96,108,'SmolVLAをドローン用にカスタマイズ',57,WHITE,560)
text(96,296,'入力を機体に合わせる',32,CYAN,500)
text(1348,296,'出力を飛行動作に合わせる',32,GOLD,500)

source=ROOT/'tmp/rescue_search/runs/eval03/clear_blue/observations/00043.jpg'
cam=Image.open(source).convert('RGB')
assert cam.size==(320,240)
im.paste(cam,(96,369))
text(96,640,'カメラ画像・言葉の指示',30,WHITE,500)
text(96,695,'機体の状態',30,WHITE,500)
text(96,743,'速度・高度・姿勢など',25,MUTED)

arrow(610,744,534,CYAN)
d.rectangle((766,362,1216,773),fill='#0e1b23',outline=LINE,width=1)
text(991,415,'SmolVLA',51,WHITE,500,'mt')
d.line((814,511,1168,511),fill=LINE,width=1)
text(991,549,'動作生成部と',30,WHITE,450,'mt')
text(991,598,'画像・言語処理の一部を',29,WHITE,450,'mt')
text(991,660,'追加学習',34,GOLD,500,'mt')
arrow(1238,1324,534,GOLD)

text(1348,394,'移動・旋回の速度',32,WHITE,500)
text(1348,449,'離陸・着陸の要求',32,WHITE,500)
for j in range(32):
 x=1348+j*14
 d.rectangle((x,584,x+8,624),fill=GOLD if j<5 else '#736b56' if j<14 else '#3b3c34')
text(1348,654,'32ステップの動作列',28,WHITE,500)
text(1348,701,'1ステップ＝0.1秒',25,MUTED)

d.line((96,848,1824,848),fill=LINE,width=1)
text(96,899,'教師データ',28,GOLD,500)
text(350,891,'シミュレーターで作成した飛行データ',35,WHITE,500)
text(350,950,'映像・指示・機体の状態と、対応する動作列を組にして学習',27,MUTED)

OUT.mkdir(parents=True,exist_ok=True)
im.save(OUT/'smolvla_customization.png')
(OUT/'smolvla_customization.json').write_text(json.dumps(dict(status='Static preview only; video unchanged',dimensions=[1920,1080],text=boxes,source_image=str(source),sources=['smolvla_policy.py','outputs/smolvla_training_realism_precision_02/started.json','outputs/smolvla_training_realism_precision_02/result.json','outputs/vla_data_realism_precision_02/manifest.json'],technical_notes=dict(action_expert_architecture_replaced=False,input_state_dimensions=9,action_dimensions=6,chunk_steps=32,action_dt_s=.1,trained_vlm_layers=[13,14],vision_encoder_frozen=True,low_level_attitude_control='ArduPilot via controller, explained on preceding slide')),ensure_ascii=False,indent=2),encoding='utf8')
print(OUT/'smolvla_customization.png')
