"""Layout v3 using recorded input pixels and actually applied policy actions."""
import os,sys,json,hashlib,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tmp/rescue_search'))
from edit_movie import Record
out=ROOT/'output/video/experiment_review';out.mkdir(exist_ok=True)
r=Record(ROOT/'tmp/rescue_search/runs/eval03/clear_blue');_,row,p,onboard=r.at(52)
a=row['model_action'];assert row['action_source']=='policy'
for k in range(3):assert abs(a[k]-p['action_chunk'][row['chunk_index']][k])<1e-7
assert abs(a[3]-p['action_chunk'][row['yaw_chunk_index']][3])<1e-7
BG='#091319';WHITE='#eef1ee';MUTED='#a9b8be';CYAN='#7ccac6';GOLD='#dfbf8a';LINE='#2b3c43'
im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
def font(n,w=450):
 f=ImageFont.truetype('C:/Windows/Fonts/NotoSansJP-VF.ttf',n);f.set_variation_by_axes([w]);return f
def text(x,y,s,n=26,c=WHITE,w=450,anchor='lt'):
 d.text((x,y),s,font=font(n,w),fill=c,anchor=anchor)
text(64,35,'捜索の実演',24,CYAN,500)
text(60,83,'「青い服の人を探して」',46,WHITE,550)
text(64,158,'外部カメラ',25,MUTED)
text(1360,158,'VLAへの入力画像',25,CYAN,500)
external=ROOT/'tmp/rescue_search/movie/renders/demo/0540.jpg'
im.paste(Image.open(external).resize((1248,780),Image.Resampling.LANCZOS),(64,198))
# Nearest-neighbour enlargement; no image enhancement.
im.paste(onboard.resize((480,360),Image.Resampling.NEAREST),(1368,198))
text(1368,575,'実際にモデルへ渡した画像',21,MUTED)
text(1368,603,'映像取得から '+f'{row["t"]-p["sim_time_capture"]:.2f} 秒',16,MUTED)
d.line((1360,623,1856,623),fill=LINE,width=1)
text(1360,645,'VLAが生成した動作',25,GOLD,500)
text(1856,650,'実行中',20,MUTED,anchor='rt')
rows=[('前進',a[0],.2,f'{a[0]:.3f} m/s'),('左移動',a[1],.2,f'{a[1]:.3f} m/s'),('上昇',a[2],.3,f'{a[2]:.3f} m/s'),('右旋回',a[3],.35,f'{math.degrees(a[3]):.2f} °/s')]
for i,(label,value,scale,number) in enumerate(rows):
 y=698+i*43
 text(1360,y,label,23)
 x0,x1=1485,1651;mid=(x0+x1)/2;cy=y+15
 d.line((x0,cy,x1,cy),fill=LINE,width=5);d.line((mid,cy-7,mid,cy+7),fill='#596a71',width=1)
 end=mid+max(-1,min(1,value/scale))*(x1-mid)
 d.line((min(mid,end),cy,max(mid,end),cy),fill=GOLD,width=5);d.ellipse((end-3,cy-3,end+3,cy+3),fill=GOLD)
 text(1856,y,number,23,WHITE,anchor='rt')
# The controller selects translation and yaw from different steps of the same chunk.
text(1360,886,'生成した動作列',19,MUTED)
for j,(label,index) in enumerate([('移動',row['chunk_index']),('旋回',row['yaw_chunk_index'])]):
 y=920+j*29;text(1360,y,label,18,MUTED)
 for k in range(32):
  x=1420+k*11.4;color=GOLD if k==index else '#52666c' if k<index else '#23353e'
  d.rectangle((x,y+4,x+7,y+16),fill=color)
 text(1856,y,f'{index+1}/32',18,GOLD,anchor='rt')
# A single restrained progress line; no future stage is marked complete.
steps=[('捜索',True),('人物を発見',True),('接近・停止',False),('確認画像を保存',False),('着陸',False)]
xs=[138,453,802,1162,1630]
d.line((148,1032,1630,1032),fill=LINE,width=2)
for i,((label,done),x) in enumerate(zip(steps,xs)):
 active=i==2;col=GOLD if active else CYAN if done else '#63767e'
 d.ellipse((x-6,1026,x+6,1038),fill=col)
 # Opaque text backing keeps the rule from crossing the letters.
 f=font(24,500 if active else 450);width=f.getlength(label)
 d.rectangle((x+17,1014,x+29+width,1054),fill=BG)
 text(x+23,1018,label,24,col,500 if active else 450)
im.save(out/'experiment_layout_v3.png')
(out/'experiment_layout_v3.json').write_text(json.dumps(dict(kind='proposed video layout',simulation_time=row['t'],phase=row['phase'],camera_sha256=p['image_sha256'],camera_file=p['image_file'],camera_capture_time=p['sim_time_capture'],camera_display_resize='nearest neighbour 320x240 to 480x360; no enhancement',displayed_actions=a,translation_chunk_index=row['chunk_index'],yaw_chunk_index=row['yaw_chunk_index'],external_frame=str(external)),ensure_ascii=False,indent=2),encoding='utf8')
print(out/'experiment_layout_v3.png')
