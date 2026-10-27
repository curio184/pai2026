"""Preview only: MuJoCo chapter card. Does not modify any video."""
import os,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT'])
OUT=ROOT/'output/video/experiment_review';OUT.mkdir(exist_ok=True)
im=Image.new('RGB',(1920,1080),'#091319');draw=ImageDraw.Draw(im)
def font(size,weight=500):
 f=ImageFont.truetype('C:/Windows/Fonts/NotoSansJP-VF.ttf',size)
 f.set_variation_by_axes([weight]);return f
draw.text((960,481),'シミュレーターでの実演',font=font(72),fill='#eef1ee',anchor='mm')
draw.text((960,603),'MuJoCo',font=font(46),fill='#7ccac6',anchor='mm')
draw.line((880,681,1040,681),fill='#7ccac6',width=2)
im.save(OUT/'simulator_demonstration_card.png')
(OUT/'simulator_demonstration_card.json').write_text(json.dumps(dict(status='preview only; video unchanged',dimensions=[1920,1080],title='シミュレーターでの実演',subtitle='MuJoCo',font='Noto Sans JP',palette=['#091319','#eef1ee','#7ccac6']),ensure_ascii=False,indent=2),encoding='utf8')
print(OUT/'simulator_demonstration_card.png')
