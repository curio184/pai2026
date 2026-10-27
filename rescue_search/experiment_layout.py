import os,sys,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tmp/rescue_search'))
from edit_movie import Record
out=ROOT/'output/video/experiment_review';out.mkdir(exist_ok=True)
r=Record(ROOT/'tmp/rescue_search/runs/eval03/clear_blue')
idx,row,packet,onboard=r.at(52)
assert onboard is not None
im=Image.new('RGB',(1920,1080),'#091319');d=ImageDraw.Draw(im)
def txt(x,y,s,n=28,color='#eef1ee',weight=450):
 f=ImageFont.truetype('C:/Windows/Fonts/NotoSansJP-VF.ttf',n);f.set_variation_by_axes([weight]);d.text((x,y),s,font=f,fill=color,anchor='lt')
txt(64,43,'捜索の実演',26,'#7ccac6',500)
txt(60,98,'「青い服の人を探して」',48,weight=550)
txt(64,191,'機体の動き',25,'#a9b8be')
txt(1360,191,'ドローンのカメラ映像',25,'#eef1ee',500)
external=ROOT/'tmp/rescue_search/movie/renders/demo/0540.jpg'
im.paste(Image.open(external).resize((1248,780),Image.Resampling.LANCZOS),(64,236))
im.paste(onboard.resize((496,372),Image.Resampling.NEAREST),(1360,236))
d.line((1360,655,1856,655),fill='#2b3b43',width=1)
txt(1360,697,'青い服の人物を発見',29,'#7ccac6',500)
txt(1360,756,'対象者に接近',34,weight=500)
txt(1360,966,'VLAが実際に受け取った画像',22,'#a9b8be')
im.save(out/'experiment_layout.png')
(out/'experiment_layout.json').write_text(json.dumps(dict(kind='layout review frame',simulation_time=row['t'],phase=row['phase'],external_frame=str(external),external_frame_sha256=hashlib.sha256(external.read_bytes()).hexdigest(),camera_packet=packet,original_camera_pixels_unmodified_before_nearest_resize=True),ensure_ascii=False,indent=2),encoding='utf8')
print(row['phase'],out/'experiment_layout.png')
