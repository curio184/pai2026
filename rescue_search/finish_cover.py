"""Native title-card typesetting, separate from the approved video master."""
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(os.environ['RESCUE_PROJECT_ROOT'])
OUT = ROOT / 'output/video/cover_layout'
OUT.mkdir(exist_ok=True)
SOURCE = ROOT / 'tmp/realism_movie/world_final/0040.jpg'
WHITE = '#f4f4ee'
GOLD = '#e9c78e'
TITLE = '災害救助ドローンの開発'
SUBTITLE = '― VLAによる自律飛行と被災者捜索 ―'
STACK = [('SmolVLA', '（動作生成）'), ('ArduPilot', '（姿勢制御）'), ('StampFly', '（ドローン）')]

def font(n, kind='jp'):
    names = {'jp':'YuGothM.ttc', 'bold':'YuGothB.ttc', 'en':'bahnschrift.ttf'}
    return ImageFont.truetype('C:/Windows/Fonts/' + names[kind], n)

def background(graded):
    im = Image.open(SOURCE).convert('RGB')
    if not graded:
        return Image.blend(im, Image.new('RGB', im.size, (4,11,17)), .56)
    a = np.asarray(im, dtype=np.float32)
    y,x = np.mgrid[:im.height,:im.width]
    # Keep the scene legible on the right and reserve calm dark areas for text.
    left = np.clip(1-x/1600, 0, 1)
    lower = np.clip((y-730)/350,0,1)
    alpha = .37 + .25*left + .15*lower
    a = a*(1-alpha[...,None]) + np.array([4,11,17])*alpha[...,None]
    return Image.fromarray(np.uint8(np.clip(a,0,255)))

def tracked(d, s, xy, f, fill, spacing):
    x,y = xy
    for c in s:
        d.text((x,y), c, font=f, fill=fill, anchor='ls')
        x += f.getlength(c)+spacing
    return x

def render(name, title_size, baseline, subtitle_size, subtitle_base, graded, stack_size, x=108):
    im=background(graded); d=ImageDraw.Draw(im); boxes=[]
    d.rectangle((65,208,73,716), fill=GOLD)
    tracked(d,'PHYSICAL AI',(x,246),font(25,'en'),GOLD,1.6)
    for s,n,k,y,col in [(TITLE,title_size,'bold',baseline,WHITE),
                        (SUBTITLE,subtitle_size,'jp',subtitle_base,'#e4e8e7')]:
        f=font(n,k); box=d.textbbox((x,y),s,font=f,anchor='ls')
        assert box[0]>=96 and box[2]<1824 and box[3]<970
        boxes.append(dict(text=s,bbox=box))
        d.text((x,y),s,font=f,fill=col,anchor='ls')
    pos=x
    for i,(model,role) in enumerate(STACK):
        if i:
            f=font(stack_size,'jp'); s='  ×  '
            d.text((pos,936),s,font=f,fill='#c2b397',anchor='ls');pos+=f.getlength(s)
        for s,kind,color in [(model,'en',GOLD),(role,'jp','#d6dedf')]:
            f=font(stack_size,kind)
            d.text((pos,936),s,font=f,fill=color,anchor='ls');pos+=f.getlength(s)
    assert pos<1824
    meta=dict(title=TITLE,subtitle=SUBTITLE,stack=' × '.join(m+r for m,r in STACK),
              title_size=title_size,subtitle_size=subtitle_size,stack_size=stack_size,
              text_boxes=boxes,stack_right=pos,background_source=str(SOURCE),
              video_modified=False)
    im.save(OUT/(name+'.png'))
    (OUT/(name+'.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
    return im

def variants():
    options=[('A',82,397,35,493,False,28),
             ('B',88,397,35,493,True,29),
             ('C',84,420,37,516,True,31)]
    sheet=Image.new('RGB',(960,3*580),(16,23,28));d=ImageDraw.Draw(sheet)
    for i,args in enumerate(options):
        im=render(*args)
        d.text((20,i*580+8),args[0],font=font(20,'en'),fill=WHITE)
        sheet.paste(im.resize((960,540),Image.Resampling.LANCZOS),(0,i*580+40))
    sheet.save(OUT/'layout_comparison.jpg',quality=94)

if __name__=='__main__':
    variants()
    final=render('title_final',88,378,36,475,True,32)
    final.resize((1280,720),Image.Resampling.LANCZOS).save(OUT/'title_final_720p.png')
    final.resize((960,540),Image.Resampling.LANCZOS).save(OUT/'title_final_540p.png')
    print(OUT)
