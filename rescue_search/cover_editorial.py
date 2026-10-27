"""Compare structurally different editorial compositions for the title card."""
from finish_cover import ROOT,SOURCE,font,tracked,WHITE,GOLD
from PIL import Image,ImageDraw
import numpy as np
import json

OUT=ROOT/'output/video/cover_editorial';OUT.mkdir(exist_ok=True)
W,H=1920,1080

def backdrop(mode):
    im=Image.open(SOURCE).convert('RGB');a=np.asarray(im,dtype=float)
    y,x=np.mgrid[:H,:W]
    if mode=='column':
        weight=1/(1+np.exp((x-840)/160))
        alpha=.19+.68*weight+.07*np.clip((y-880)/200,0,1)
    elif mode=='header':
        alpha=.20+.58*np.exp(-(y/360)**2)+.53*np.clip((y-780)/220,0,1)
    else:
        alpha=.22+np.zeros((H,W))
    a=a*(1-alpha[...,None])+np.array([7,16,22])*alpha[...,None]
    im=Image.fromarray(np.uint8(np.clip(a,0,255)))
    if mode=='split':ImageDraw.Draw(im).rectangle((0,0,875,H),fill='#0b151b')
    return im

def put(d,s,x,y,n,kind='jp',fill=WHITE):
    d.text((x,y),s,font=font(n,kind),fill=fill,anchor='ls')

def tech_columns(d,x,y,step,size=31):
    for i,(name,role) in enumerate([('SmolVLA','（動作生成）'),('ArduPilot','（姿勢制御）'),('StampFly','（ドローン）')]):
        put(d,name,x+i*step,y,size,'en',GOLD)
        put(d,role,x+i*step,y+43,24,fill='#b9c6ca')
        if i<2:put(d,'×',x+(i+1)*step-52,y+14,24,fill='#76868c')

def column(final=False):
    im=backdrop('column');d=ImageDraw.Draw(im)
    x=140
    d.rectangle((88,257,94,612),fill=GOLD)
    tracked(d,'PHYSICAL AI',(x,285),font(25,'en'),GOLD,2.2)
    put(d,'災害救助',x,403,88,'bold')
    put(d,'ドローンの開発',x,514,88,'bold')
    put(d,'― VLAによる自律飛行と被災者捜索 ―',x,601,31,fill='#dae1e2')
    d.line((x,680,775,680),fill='#39484e',width=1)
    if final:
        for i,(name,role) in enumerate([('SmolVLA','（動作生成）'),('ArduPilot','（姿勢制御）'),('StampFly','（ドローン）')]):
            center=235+i*222
            put(d,name,center-font(33,'en').getlength(name)/2,750,33,'en',GOLD)
            put(d,role,center-font(25).getlength(role)/2,794,25,fill='#c4cfd2')
            if i<2:
                put(d,'×',center+111-font(24).getlength('×')/2,775,24,fill='#819097')
    else:
        tech_columns(d,x,750,229,31)
    return im

def header():
    im=backdrop('header');d=ImageDraw.Draw(im)
    d.rectangle((88,91,94,293),fill=GOLD)
    tracked(d,'PHYSICAL AI',(140,118),font(25,'en'),GOLD,2.2)
    put(d,'災害救助ドローンの開発',140,218,78,'bold')
    put(d,'― VLAによる自律飛行と被災者捜索 ―',140,290,33,fill='#dae1e2')
    d.line((140,889,1780,889),fill='#526065',width=1)
    tech_columns(d,140,950,560,33)
    return im

def split():
    im=backdrop('split');d=ImageDraw.Draw(im)
    d.rectangle((72,222,78,565),fill=GOLD)
    tracked(d,'PHYSICAL AI',(120,251),font(25,'en'),GOLD,2.2)
    put(d,'災害救助',120,368,84,'bold')
    put(d,'ドローンの開発',120,478,84,'bold')
    put(d,'― VLAによる自律飛行と被災者捜索 ―',120,560,29,fill='#dae1e2')
    tech_columns(d,120,772,229,31)
    return im

if __name__=='__main__':
    sheet=Image.new('RGB',(1152,3*688),'#111b22');d=ImageDraw.Draw(sheet)
    for i,(name,fn) in enumerate([('A',column),('B',header),('C',split)]):
        im=fn();im.save(OUT/(name+'.png'))
        put(d,name,20,i*688+29,22,'en')
        sheet.paste(im.resize((1152,648),Image.Resampling.LANCZOS),(0,i*688+40))
    sheet.save(OUT/'composition_comparison.jpg',quality=95)
    final=column(True)
    final.save(OUT/'cover_refined.png')
    final.resize((960,540),Image.Resampling.LANCZOS).save(OUT/'cover_refined_540p.png')
    (OUT/'design_notes.json').write_text(json.dumps(dict(
        chosen_composition='A: grouped left typography with continuous scene on right',
        refinements=['Centered names and roles in three equal columns',
                     'Aligned separators with visual center between names and roles',
                     'Bar follows the title block, not unused space',
                     'Background luminance reserves a readable region for text'],
        video_modified=False),indent=2),encoding='utf8')
    print(OUT)
