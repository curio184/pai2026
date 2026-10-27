"""Produce a cinematic, source-bound edit of existing successful flight records.

No inference, physics integration, scoring, contacts or external services run here.
All flight poses, camera inputs, actions and metrics come from immutable records.
Studio graphics and moving replay cameras are presentation, explicitly labeled.
"""
import argparse
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import wave
import xml.etree.ElementTree as ET

import imageio.v2 as imageio
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from make_demo_video import FlightRecord
from rescue_scene import portable_asset_path

ROOT=Path(__file__).resolve().parent
TMP=ROOT/'tmp/premium'
OUT=ROOT/'output/video'
RECORDS=ROOT/'outputs/ardupilot/inference_revision_04'
W,H,FPS,DURATION=1920,1080,30,158
BG='#07121d';PANEL='#0c1d2b';LINE='#244051'
WHITE='#f3f7fa';MUTED='#9aafbf';CYAN='#5fe5d1';BLUE='#68b7ff';RED='#ff8a80';GOLD='#f7c484'
CHECKPOINT='92b06f3426fd9d13c9a792eaa512b6df49e0b338cc8df5791dd1c07fd73daf7f'
LABELS={'takeoff':'離陸して','hover':'その場で止まって','blue':'青い服の人の前で止まって',
        'red':'赤い服の人の前で止まって','right':'右に90度回って','left':'左に90度回って','land':'着陸して'}
TIMELINE=[('hero',0,8),('premise',8,16),('architecture',16,31),('blue',31,56),
          ('red',56,81),('turns',81,110),('left',110,131),('results',131,145),('outro',145,158)]
NARRATION=[
    (1.0,5.8,'ことばが、飛行になる。','ことばが、飛行になる。'),
    (8.3,7.2,'青い服の人の前で、止まって。カメラを見て、指示に応じて動く、救助ドローンです。','カメラを見て、ことばに応じて飛ぶ。'),
    (16.7,8.0,'画像とことば、機体の状態から、学習済みのスモール、ブイエルエーが、飛行アクションを生成します。','画像 ＋ ことば ＋ 自己状態 → 学習済みSmolVLA → 飛行アクション'),
    (25.0,5.5,'姿勢の安定化は、アルデュパイロット。飛行を、物理シミュレーションで確かめます。','姿勢を安定化し、物理シミュレーションで飛行。'),
    (32.0,6.8,'まずは青。離陸して、空中で静止。次の指示を待ちます。','離陸 → 空中で静止 → 指示された人へ。'),
    (40.3,8.8,'青い服の人へ接近し、その手前で止まる。右側は、モデルが実際に受け取った画像です。','右側は、モデルが実際に受け取った入力画像。'),
    (50.0,5.0,'三秒以上の静止を確認し、着陸します。','人の手前で3秒以上静止し、着陸。'),
    (57.0,7.8,'次は赤。同じモデルが、ことばに合わせて、進む方向を切り替えます。','同じモデルが、指示に合わせて進む方向を変える。'),
    (74.0,5.5,'赤い服の人の前でも静止。その後、着陸まで完了しました。','赤い服の人への接近・静止・着陸も完了。'),
    (82.0,7.5,'移動だけではありません。右に九十度。回り終えたら、その場で止まります。','右へ90度。回り終えたら、その場で停止。'),
    (99.0,7.8,'続いて左へ。同じ飛行の中で、逆方向の指示にも応答します。','続いて左へ。同じ飛行の中で逆方向にも応答。'),
    (111.0,7.8,'左旋回だけの独立した飛行も確認。離陸から着陸まで、同じ最終モデルで実行しています。','独立した左旋回も、同じ最終モデルで実行。'),
    (132.0,9.5,'四つの機能確認がすべて成功。停止時間や回転角は、飛行後の物理ログから、別に採点しました。','4つの機能確認がすべて成功。物理ログから独立に採点。'),
    (146.0,10.0,'これは、既知の仮想環境での成果です。実機への搭載は未検証。見る、理解する、飛ぶ。そのつながりを、ここまで実装しました。','見る。理解する。飛ぶ。カメラと言語から、身体の動きへ。')
]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def smooth(x):x=max(0,min(1,float(x)));return x*x*(3-2*x)
def mix(a,b,t):return np.asarray(a)*(1-t)+np.asarray(b)*t
def rgb(c):return tuple(bytes.fromhex(c.lstrip('#')))

@lru_cache(maxsize=160)
def font(size,kind='jp'):
    name={'jp':'YuGothM.ttc','bold':'YuGothB.ttc','en':'bahnschrift.ttf','light':'segoeuil.ttf'}[kind]
    return ImageFont.truetype(str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/name),int(size))

def txt(im,xy,value,size=28,color=WHITE,kind='jp',anchor=None):
    ImageDraw.Draw(im).text(xy,str(value),font=font(size,kind),fill=color,anchor=anchor,stroke_width=0)

def rounded(im,box,fill=PANEL,outline=None,r=20,width=1):
    ImageDraw.Draw(im).rounded_rectangle(tuple(map(int,box)),radius=r,fill=fill,outline=outline,width=width)

def line(im,points,color=LINE,width=2):ImageDraw.Draw(im).line(points,fill=color,width=width)

@lru_cache(maxsize=2)
def base():
    yy,xx=np.mgrid[0:H,0:W]
    glow=np.exp(-(((xx-1380)/1050)**2+((yy-240)/700)**2))
    a=np.zeros((H,W,3),np.float32)
    for i,c in enumerate((6,15,25)):a[:,:,i]=c+glow*(5,15,20)[i]
    im=Image.fromarray(np.uint8(np.clip(a,0,255)))
    d=ImageDraw.Draw(im)
    for x in range(64,W,112):
        for y in range(80,H,112):d.ellipse((x,y,x+2,y+2),fill='#203545')
    return im

def footer(im,t,section,mode='SIMULATION / RECORDED FLIGHT'):
    line(im,[(64,1024),(1856,1024)],LINE)
    txt(im,(64,1038),'RESCUE / VLA',18,CYAN,'en')
    txt(im,(310,1038),mode,17,MUTED,'en')
    txt(im,(1856,1038),f'{section.upper()}  /  {int(t)//60:02}:{int(t)%60:02}',18,MUTED,'en',anchor='ra')
    ImageDraw.Draw(im).rectangle((64,1023,64+int(1792*t/DURATION),1025),fill=CYAN)

def pill(im,xy,label,color=CYAN,size=19,width=None):
    box=font(size,'en').getbbox(label)
    width=width or box[2]+30
    x,y=xy;rounded(im,(x,y,x+width,y+34),BG,color,8)
    txt(im,(x+14,y+5),label,size,color,'en')

def caption(im,t,voices):
    active=None
    for v in voices:
        if v['start']<=t<=v['start']+v.get('duration_s',v['max_s'])+.20:active=v
    if not active:return
    value=active['caption']
    f=font(29,'bold');width=f.getlength(value)
    if width>1760:raise ValueError('Subtitle exceeds safe area')
    x=(W-width)/2
    rounded(im,(x-30,951,x+width+30,1008),'#06101b',r=12)
    txt(im,(x,960),value,29,WHITE,'bold')

def fit(im,size):return im.resize(size,Image.Resampling.LANCZOS)

@lru_cache(maxsize=4)
def studio(name):return Image.open(TMP/f'{name}.png').convert('RGB')

def studio_back(name,t,zoom=1.0):
    folder='opening' if name=='hero' else 'closing'
    count=240 if folder=='opening' else 390
    index=min(count-1,max(0,int(round((t if folder=='opening' else t-145)*FPS))))
    animated=TMP/folder/f'{index:04}.jpg'
    if animated.exists():return Image.open(animated).convert('RGB')
    src=studio(name);z=zoom
    cw,ch=round(src.width/z),round(src.height/z)
    cx=src.width*(.5+.015*math.sin(t*.16));cy=src.height*.5
    return src.crop((round(cx-cw/2),round(cy-ch/2),round(cx+cw/2),round(cy+ch/2))).resize((W,H),Image.Resampling.LANCZOS)

def shade(im,left=True,bottom=True):
    # Only graphic compositing: this never changes the recorded model inputs.
    overlay=np.zeros((H,W,4),np.uint8);overlay[:,:,:3]=(3,10,18)
    alpha=np.zeros((H,W),np.float32)
    if left:alpha+=np.linspace(.92,.0,W)[None,:]**1.1*255
    if bottom:alpha+=np.clip((np.arange(H)-720)/360,0,.8)[:,None]*255
    overlay[:,:,3]=np.uint8(np.clip(alpha,0,245))
    return Image.alpha_composite(im.convert('RGBA'),Image.fromarray(overlay)).convert('RGB')

class CinematicView:
    """A separate, display-only MjModel; mj_forward but NEVER mj_step."""
    def __init__(self):
        tree=ET.parse(RECORDS/'rescue_scene.xml');root=tree.getroot()
        root.find('compiler').set('meshdir',portable_asset_path(root.find('compiler').get('meshdir')))
        ET.SubElement(root,'statistic',extent='6',center='1.5 0 .8')
        visual=root.find('visual')
        visual.find('global').set('offwidth','1280');visual.find('global').set('offheight','900')
        visual.find('headlight').attrib.update(ambient='.28 .32 .38',diffuse='.5 .55 .6',specular='.4 .45 .5')
        ET.SubElement(visual,'quality',shadowsize='4096',offsamples='4')
        ET.SubElement(visual,'map',fogstart='4',fogend='20',znear='.001',zfar='100')
        ET.SubElement(visual,'rgba',haze='.025 .055 .08 1',fog='.025 .055 .08 1')
        # Restrained meter grid instead of the original high-frequency checker.
        tex=Image.new('RGB',(1024,1024),'#12232d');d=ImageDraw.Draw(tex)
        for x in range(0,1024,256):
            d.line((x,0,x,1024),fill='#29424e',width=2);d.line((0,x,1024,x),fill='#29424e',width=2)
        tex.save(TMP/'replay_floor.png')
        a=root.find('asset')
        old=a.find('texture[@name="grid"]');a.remove(old)
        ET.SubElement(a,'texture',name='grid',type='2d',file='replay_floor.png')
        a.find('material[@name="grid"]').attrib.update(texrepeat='100 100',reflectance='.08',shininess='.2')
        world=root.find('worldbody')
        for light in list(world.findall('light')):world.remove(light)
        ET.SubElement(world,'light',pos='0 -2 6',dir='.25 .2 -1',diffuse='.8 .86 1',specular='.5 .6 .7',castshadow='true',directional='true')
        ET.SubElement(world,'light',pos='4 3 3',dir='-1 -.3 -.5',diffuse='.25 .7 .75',specular='.2 .4 .5',castshadow='false')
        self.model=mujoco.MjModel.from_xml_string(ET.tostring(root,encoding='unicode'),assets={'replay_floor.png':(TMP/'replay_floor.png').read_bytes()})
        self.data=mujoco.MjData(self.model);self.options=mujoco.MjvOption()
        for name in ('back_wall','left_wall','right_wall'):
            idx=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_GEOM,name)
            self.model.geom_group[idx]=5
        self.options.geomgroup[5]=0
        self.renderer=mujoco.Renderer(self.model,width=1280,height=900)
        self.camera=mujoco.MjvCamera();self.camera.type=mujoco.mjtCamera.mjCAMERA_FREE
        self.camera_params=[]

    def render(self,record,row,index,local,profile):
        self.data.qpos[:]=row['truth'][19:26];self.data.qvel[:]=row['truth'][26:32]
        mujoco.mj_forward(self.model,self.data)
        p=np.asarray(row['truth'][19:22]);phase=row['phase']
        if phase in ('takeoff','hover','land'):
            target=p+np.array([.025,0,-.02]);distance=.55 if phase=='land' else .60
            azimuth=142+2*math.sin(local*.22);elevation=-24
            if phase=='takeoff' and row['t']<22:distance=.70
        elif phase in ('right','left'):
            target=p;distance=.52;azimuth=155;elevation=-59
        else:
            # A wide, stable scene view preserves both people and the route.
            # A separately labeled close-up below resolves the tiny airframe.
            target=np.array([(p[0]+3.15)/2,p[1]*.85,.62]);distance=3.60
            azimuth=-4;elevation=-19
        self.camera.lookat[:]=target;self.camera.distance=distance
        self.camera.azimuth=azimuth;self.camera.elevation=elevation
        self.renderer.update_scene(self.data,camera=self.camera,scene_option=self.options)
        # A short route trace in the display model, never a navigation observation.
        if phase in ('blue','red'):
            trail=[r['truth'][19:22] for r in record.rows[max(0,index-500):index:24]]
            for position in trail:
                s=self.renderer.scene
                if s.ngeom>=s.maxgeom:break
                mujoco.mjv_initGeom(s.geoms[s.ngeom],mujoco.mjtGeom.mjGEOM_SPHERE,np.array([.008,0,0]),np.array(position),np.eye(3).ravel(),np.array([.2,.9,.8,.7]))
                s.ngeom+=1
        cam=self.renderer.scene.camera[0]
        rel=p-np.asarray(cam.pos);forward=np.asarray(cam.forward);up=np.asarray(cam.up)
        right=np.cross(forward,up);z=float(np.dot(rel,forward))
        tangent=float(cam.frustum_top-cam.frustum_bottom)/(2*float(cam.frustum_near))
        self.projected=(640+float(np.dot(rel,right))/z/tangent/2*900,450-float(np.dot(rel,up))/z/tangent/2*900)
        return Image.fromarray(self.renderer.render().copy())

    def closeup(self):
        self.camera.lookat[:]=self.data.qpos[:3]+np.array([0,0,-.005])
        self.camera.distance=.34;self.camera.azimuth=140;self.camera.elevation=-26
        self.renderer.update_scene(self.data,camera=self.camera,scene_option=self.options)
        return Image.fromarray(self.renderer.render().copy()).resize((300,211),Image.Resampling.LANCZOS)

    def close(self):self.renderer.close()

class Production:
    def __init__(self):
        TMP.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
        manifest=json.loads((RECORDS/'verification_manifest.json').read_text(encoding='utf8'))
        assert manifest['checkpoint_sha256']==CHECKPOINT
        self.records={p:FlightRecord(RECORDS/p) for p in ('blue','red','turns','left')}
        self.inputs_verified=set();self.phase_begin={};self.streaks={};self.yaws={}
        for p,r in self.records.items():
            assert r.score['success'] and r.score['checkpoints']==[CHECKPOINT]
            begin={};streak=[];elapsed=0;hold_start=None
            for row in r.rows:
                begin.setdefault(row['phase'],row['t'])
                if p in ('blue','red'):
                    goal=r.score['goal_holds'][p]['goal_scene_xy_m']
                    dist=np.linalg.norm(np.asarray([row['truth'][2],row['truth'][1]])-goal)
                    v=np.linalg.norm(row['truth'][4:6]);alt=-row['truth'][3]
                    valid=row['phase']==p and dist<=.25 and v<=.08 and .8<=alt<=1.25
                    if valid:
                        if hold_start is None:hold_start=row['t']
                        elapsed=row['t']-hold_start
                    else:hold_start=None;elapsed=0
                streak.append(elapsed)
            self.phase_begin[p]=begin;self.streaks[p]=streak
            # Truth quaternion in the NED record, matching the independent scorer.
            q=np.asarray([row['truth'][7:11] for row in r.rows])
            self.yaws[p]=np.unwrap(np.arctan2(2*(q[:,0]*q[:,3]+q[:,1]*q[:,2]),1-2*(q[:,2]**2+q[:,3]**2)))
        self.view=CinematicView()
        voicepath=TMP/'voice_manifest.json'
        self.voices=json.loads(voicepath.read_text(encoding='utf8')) if voicepath.exists() else [dict(start=s,max_s=m,text=t,caption=c) for s,m,t,c in NARRATION]

    def map(self,im,p,index,box=(72,660,414,856)):
        x,y,x2,y2=box;rounded(im,box,'#091825',LINE,14)
        txt(im,(x+16,y+11),'TRAJECTORY / LOG',16,MUTED,'en')
        def point(a,b):return (x+30+(a+.4)/4.1*(x2-x-60),y2-25-(b+1.15)/2.3*(y2-y-64))
        r=self.records[p];points=[point(*z['truth'][19:21]) for z in r.rows[:index+1:30]]
        if len(points)>1:line(im,points,CYAN,3)
        d=ImageDraw.Draw(im)
        for color,col in [('blue',BLUE),('red',RED)]:
            a,b=r.score['goal_holds'][color]['goal_scene_xy_m'];px,py=point(a+.9,b)
            d.ellipse((px-5,py-5,px+5,py+5),fill=col)
        px,py=point(*r.rows[index]['truth'][19:21]);d.ellipse((px-5,py-5,px+5,py+5),fill=WHITE)
        px,py=point(0,0);d.ellipse((px-3,py-3,px+3,py+3),outline=MUTED,width=1)

    def hero(self,t):
        im=shade(studio_back('hero',t,1.0+.045*smooth(t/8)))
        a=smooth((t-.4)/1.8)
        txt(im,(77,91),'PHYSICAL AI / FINAL PROJECT',23,CYAN,'en')
        line(im,[(80,161),(270,161)],CYAN,3)
        txt(im,(73,220+int((1-a)*40)),'ことばが、',88,WHITE,'bold')
        txt(im,(73,342+int((1-a)*40)),'飛行になる。',88,WHITE,'bold')
        txt(im,(79,504),'RESCUE / VLA',39,CYAN,'en')
        txt(im,(80,577),'カメラと言語で動く、小さな救助ドローン。',28,WHITE)
        pill(im,(80,655),'SmolVLA  /  ArduPilot  /  MuJoCo',CYAN,19,435)
        txt(im,(80,883),'StampFly機体メッシュを用いたスタジオCG',19,MUTED)
        txt(im,(80,916),'追加センサーの外観は模式表現 / 実機映像ではありません',18,MUTED)
        footer(im,t,'Opening','STUDIO VISUALIZATION');return im

    def premise(self,t):
        u=t-8;im=base().copy()
        txt(im,(72,79),'01 / THE IDEA',22,CYAN,'en')
        txt(im,(69,132),'同じ景色。指示が変わる。',62,WHITE,'bold')
        for i,(p,col,word) in enumerate([('blue',BLUE,'青'),('red',RED,'赤')]):
            x=72+i*912;r=self.records[p]
            _,row,packet,img=r.at(self.phase_begin[p][p]+1.4)
            if img is not None:
                img=img.resize((768,576),Image.Resampling.NEAREST)
                im.paste(img,(x+28,300))
            rounded(im,(x,246,x+864,913),None,LINE,20,2)
            pill(im,(x+28,265),'RECORDED MODEL INPUT',MUTED,16,270)
            txt(im,(x+28,814),f'「{word}い服の人の前で止まって」',35,col,'bold')
            # Mask only the overlaid caption area, never the actual evidence shot.
            rounded(im,(x+28,866,x+836,901),BG,r=4)
            txt(im,(x+42,871),'入力画像は各飛行の実記録 / 同じ配置の仮想環境',18,MUTED)
        footer(im,t,'The idea','RECORDED CAMERA INPUTS');return im

    def architecture(self,t):
        u=t-16;im=base().copy()
        txt(im,(72,79),'02 / HOW IT WORKS',22,CYAN,'en')
        txt(im,(68,132),'見る。理解する。動く。',62,WHITE,'bold')
        specs=[(300,'01','CAMERA','前方カメラ画像',BLUE),(470,'02','LANGUAGE','青い服の人の前で止まって',CYAN),(640,'03','STATE','機体の自己推定状態 · 9次元',GOLD)]
        for y,n,title,sub,col in specs:
            rounded(im,(72,y,543,y+136),PANEL,LINE,18)
            txt(im,(95,y+19),n,26,col,'en');txt(im,(152,y+17),title,29,WHITE,'en')
            txt(im,(96,y+74),sub,24,MUTED)
            line(im,[(543,y+68),(620,y+68),(670,530)],LINE,2)
            phase=((u*.17+(y-300)/600)%1)
            px=543+(670-543)*phase;py=(y+68)+(530-y-68)*phase
            ImageDraw.Draw(im).ellipse((px-5,py-5,px+5,py+5),fill=col)
        rounded(im,(676,324,1184,749),'#103037',CYAN,24,2)
        txt(im,(716,362),'VISION · LANGUAGE · ACTION',19,CYAN,'en')
        txt(im,(716,410),'SmolVLA',69,WHITE,'en')
        txt(im,(720,505),'450M',65,CYAN,'en')
        txt(im,(923,538),'parameters',20,MUTED,'en')
        txt(im,(719,604),'学習済みの同じ最終モデル',26,WHITE,'bold')
        txt(im,(720,655),'画像・ことば・自己状態 → 行動チャンク',21,MUTED)
        line(im,[(1184,530),(1325,530)],CYAN,3)
        d=ImageDraw.Draw(im);d.polygon([(1325,530),(1312,522),(1312,538)],fill=CYAN)
        rounded(im,(1343,324,1848,749),PANEL,LINE,24)
        txt(im,(1377,360),'ACTION / 6 OUTPUTS',24,CYAN,'en')
        for i,(s,eng) in enumerate([('前後・左右・上下','VELOCITY'),('右旋回・左旋回','YAW RATE'),('離陸・着陸','REQUEST')]):
            y=424+i*96;txt(im,(1379,y),s,28,WHITE,'bold');txt(im,(1380,y+43),eng,18,MUTED,'en')
        rounded(im,(350,818,1570,897),'#10212e',LINE,18)
        txt(im,(390,839),'ArduPilot',31,WHITE,'en');txt(im,(595,846),'姿勢・高度を安定化',23,MUTED)
        txt(im,(921,838),'→',32,CYAN);txt(im,(994,839),'MuJoCo',31,WHITE,'en');txt(im,(1194,846),'物理シミュレーション',23,MUTED)
        footer(im,t,'How it works','RGB + LANGUAGE + OWN STATE → ACTION');return im

    def flight(self,t,p,start,end):
        local=t-start;r=self.records[p]
        # Exactly continuous, fixed 2x playback, from 16 s through the last row.
        moment=min(float(r.times[-1]),16+max(0,local-1.2)*2)
        index,row,packet,onboard=r.at(moment)
        im=base().copy()
        view=self.view.render(r,row,index,local,p)
        im.paste(view,(0,80))
        # The cinematic view is separated from the unmodified recorded input.
        overlay=Image.new('RGBA',(W,H),(0,0,0,0));od=ImageDraw.Draw(overlay)
        od.rectangle((0,0,1920,202),fill=(5,15,25,236))
        od.rectangle((0,865,1920,1080),fill=(5,15,25,246))
        im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')
        number={'blue':'01','red':'02','turns':'03','left':'04'}[p]
        color=BLUE if p=='blue' else RED if p=='red' else CYAN
        title={'blue':'青い服の人を探す','red':'赤い服の人を探す','turns':'右へ。そして左へ。','left':'左旋回を、単独でも。'}[p]
        txt(im,(64,35),f'FLIGHT {number} / ONE FINAL MODEL',22,color,'en')
        txt(im,(60,83),title,48,WHITE,'bold')
        txt(im,(64,150),f'指示「{LABELS[row["phase"]]}」',29,color,'bold')
        pill(im,(1310,40),'SIMULATION  /  2× REPLAY',CYAN,19,535)
        txt(im,(1310,91),f'SIM  {row["t"]:05.2f} s',29,WHITE,'en')
        txt(im,(1310,140),'初期化0–16秒のみ省略 / 以後は連続再生',20,MUTED)
        rounded(im,(1308,212,1855,866),'#081724',LINE,20)
        txt(im,(1331,231),'MODEL INPUT',21,CYAN,'en')
        txt(im,(1832,231),'実際の入力画像',19,MUTED,anchor='ra')
        if onboard is not None:
            im.paste(onboard.resize((500,375),Image.Resampling.NEAREST),(1332,275))
            self.inputs_verified.add((p,packet['image_file'],packet['image_sha256']))
        else:
            txt(im,(1380,433),'入力画像の受信待ち',26,MUTED)
        age=row['t']-packet['sim_time_capture'] if packet else 0
        txt(im,(1332,667),f'CAPTURE  {packet["sim_time_capture"]:05.2f} s' if packet else 'CAPTURE —',18,MUTED,'en')
        txt(im,(1832,667),f'AGE {age:.2f} s',19,GOLD,'en',anchor='ra')
        line(im,[(1332,702),(1832,702)],LINE)
        a=row['model_action']
        txt(im,(1332,719),'RECORDED POLICY COMMAND',17,MUTED,'en')
        for i,(label,val,lim) in enumerate([('FWD',a[0],.2),('LEFT',a[1],.2),('UP',a[2],.3)]):
            x=1334+i*167;txt(im,(x,750),label,17,MUTED,'en');txt(im,(x,777),f'{val:+.2f}',31,WHITE,'en')
            line(im,[(x,824),(x+132,824)],LINE,4)
            line(im,[(x+66,824),(x+66+int(62*np.clip(val/lim,-1,1)),824)],CYAN,4)
        txt(im,(1748,838),'m/s',14,MUTED,'en')
        phase=row['phase']
        if p in ('blue','red'):
            if phase in ('blue','red'):
                px,py=self.view.projected;py+=80
                ImageDraw.Draw(im).ellipse((px-20,py-20,px+20,py+20),outline=CYAN,width=2)
                pill(im,(int(px+28),int(py-17)),'STAMPFLY',CYAN,16,140)
                close=self.view.closeup();im.paste(close,(920,414))
                rounded(im,(918,378,1222,628),None,LINE,12,2)
                rounded(im,(920,378,1220,412),BG,r=4)
                txt(im,(933,383),'AIRFRAME / CLOSE-UP',17,CYAN,'en')
            self.map(im,p,index)
            goal=r.score['goal_holds'][p]['goal_scene_xy_m']
            distance=float(np.linalg.norm(np.asarray([row['truth'][2],row['truth'][1]])-goal))
            txt(im,(465,717),'目標点まで',21,MUTED)
            txt(im,(465,753),f'{distance:.2f}',58,WHITE,'en');txt(im,(628,787),'m',23,MUTED,'en')
            held=self.streaks[p][index]
            achieved=phase=='land' or held>=3
            rounded(im,(757,696,1210,836),'#081724',LINE,16)
            txt(im,(782,714),'PHYSICAL HOLD',17,MUTED,'en')
            display=r.score['goal_holds'][p]['physical_hold']['duration_s'] if achieved else min(3,held)
            txt(im,(782,746),f'{display:.2f}',54,CYAN if achieved else WHITE,'en')
            txt(im,(934,778),'s',24,MUTED,'en')
            txt(im,(1003,778),'確認済み' if achieved else '/ 3.00 s',22,CYAN if achieved else MUTED,'jp' if achieved else 'en')
        elif phase in ('right','left'):
            startidx=np.searchsorted(r.times,self.phase_begin[p][phase])
            delta=math.degrees(self.yaws[p][index]-self.yaws[p][startidx])
            rounded(im,(72,682,550,848),'#081724',LINE,16)
            txt(im,(98,699),'MEASURED ROTATION',18,MUTED,'en')
            txt(im,(95,736),f'{delta:+.1f}',66,CYAN,'en');txt(im,(350,779),'deg',26,MUTED,'en')
            txt(im,(650,746),f'YAW COMMAND  {math.degrees(a[3]):+.1f} deg/s',26,WHITE,'en')
        else:
            self.map(im,p,index)
        # Physical measurements are clearly separated from model commands.
        height=-row['truth'][3];speed=np.linalg.norm(row['truth'][4:6])
        txt(im,(64,890),f'ALT  {height:.2f} m',26,WHITE,'en')
        txt(im,(335,890),f'SPEED  {speed:.2f} m/s',26,WHITE,'en')
        stages=['takeoff','hover',p if p in ('blue','red') else 'turn','land']
        stage=0 if phase=='takeoff' else 1 if phase=='hover' else 3 if phase=='land' else 2
        stage_names=['離陸','静止','接近' if p in ('blue','red') else '旋回','着陸']
        for j,name in enumerate(stage_names):
            x=855+j*245
            d=ImageDraw.Draw(im);d.ellipse((x,895,x+12,907),fill=color if j<=stage else LINE)
            txt(im,(x+24,886),name,23,WHITE if j==stage else MUTED)
            if j<3:line(im,[(x+96,901),(x+214,901)],color if j<stage else LINE,2)
        txt(im,(65,931),'外部視点の壁・床・照明は表示用に調整 / 軌跡と接写は可視化のための表示',16,MUTED)
        done=local>1.2+(r.times[-1]-16)/2
        if done:
            rounded(im,(720,330,1245,527),'#092b2c',CYAN,22,2)
            txt(im,(745,347),'FLIGHT COMPLETE',30,CYAN,'en')
            txt(im,(745,405),'着陸・モーター停止を確認',32,WHITE,'bold')
            txt(im,(747,472),'PHYSICAL LOG CHECK  /  PASS',20,CYAN,'en')
        if local<1.2:
            pill(im,(777,330),f'CASE {number} / START',color,22,400)
        footer(im,t,'Flight '+number);return im

    def results(self,t):
        u=t-131;im=base().copy()
        txt(im,(72,77),'07 / VERIFIED IN PHYSICS',23,CYAN,'en')
        txt(im,(68,129),'ことばから行動へ。4つの確認。',59,WHITE,'bold')
        info=[('01','BLUE','青い服の人','3.03','秒 静止',BLUE),('02','RED','赤い服の人','3.17','秒 静止',RED),
              ('03','RIGHT / LEFT','右旋回 → 左旋回','+94.6° / -95.6°','両方向で停止',CYAN),('04','LEFT / SOLO','独立した左旋回','-92.9°','旋回後に停止',CYAN)]
        for i,(n,eng,title,big,sub,col) in enumerate(info):
            x=72+(i%2)*912;y=257+(i//2)*277
            rounded(im,(x,y,x+864,y+249),PANEL,LINE,20)
            txt(im,(x+27,y+20),n,30,col,'en');txt(im,(x+96,y+24),eng,23,MUTED,'en')
            txt(im,(x+28,y+69),title,27,WHITE,'bold')
            txt(im,(x+27,y+117),big,58 if i!=2 else 47,col,'en')
            txt(im,(x+29,y+196),sub,22,MUTED)
            if u>i*.6+.4:pill(im,(x+686,y+23),'PASS',col,19,145)
        txt(im,(77,846),'全ケース：離陸 → 指示動作 → 着陸 → モーター停止',31,WHITE,'bold')
        txt(im,(77,904),'接近の停止条件：目標点から25 cm以内・水平速度0.08 m/s以下・3秒以上',24,MUTED)
        footer(im,t,'Results','KNOWN SYNTHETIC SCENE / FUNCTIONAL CHECKS');return im

    def outro(self,t):
        u=t-145;im=shade(studio_back('detail',t,1.0+.04*smooth(u/13)))
        txt(im,(77,80),'RESCUE / VLA',26,CYAN,'en')
        txt(im,(73,185),'見る。',79,WHITE,'bold')
        txt(im,(73,288),'理解する。',79,WHITE,'bold')
        txt(im,(73,391),'飛ぶ。',79,WHITE,'bold')
        txt(im,(80,539),'小さな機体に、ことばで目的を。',32,WHITE,'bold')
        pill(im,(80,610),'4 / 4 FUNCTIONAL CHECKS PASSED',CYAN,21,534)
        rounded(im,(75,721,1020,914),'#081724',LINE,16)
        txt(im,(98,738),'今回示した範囲',25,CYAN,'bold')
        txt(im,(98,784),'既知の仮想環境での機能確認。実機飛行は行っていません。',24,WHITE)
        txt(im,(98,827),'搭載余力・カメラ電力・無線同時動作は未検証。',23,MUTED)
        txt(im,(98,867),'機体CG・外観上の追加センサーは説明用の表現です。',21,MUTED)
        footer(im,t,'Closing','SmolVLA + ArduPilot + MuJoCo');return im

    def frame(self,t):
        for name,start,end in TIMELINE:
            if start<=t<end:
                if name in self.records:im=self.flight(t,name,start,end)
                else:im=getattr(self,name)(t)
                # Short dissolve from deep navy at chapter boundaries; no fake motion.
                if start and t-start<.20:im=Image.blend(base(),im,smooth((t-start)/.20))
                if t<.5:im=Image.blend(Image.new('RGB',(W,H),BG),im,smooth(t/.5))
                if t>DURATION-1:im=Image.blend(im,Image.new('RGB',(W,H),BG),smooth(t-DURATION+1))
                caption(im,t,self.voices)
                return im
        raise ValueError(t)

    def close(self):self.view.close()

def write_voice_script():
    TMP.mkdir(parents=True,exist_ok=True)
    data=[dict(index=i,start=s,max_s=m,text=t,caption=c,file=f'voice_{i:02}.wav') for i,(s,m,t,c) in enumerate(NARRATION)]
    (TMP/'narration_plan.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    print('NARRATION_PLAN',len(data),flush=True)

def wave_read(path,sr=48000):
    with wave.open(str(path),'rb') as w:
        source=w.getframerate();channels=w.getnchannels();width=w.getsampwidth()
        assert width==2
        a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32)/32768
        if channels>1:a=a.reshape(-1,channels).mean(axis=1)
    if source!=sr:a=np.interp(np.arange(round(len(a)*sr/source))*source/sr,np.arange(len(a)),a).astype(np.float32)
    return a

def wave_write(path,arr,sr=48000):
    with wave.open(str(path),'wb') as f:
        f.setnchannels(2 if arr.ndim==2 else 1);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes(np.int16(np.clip(arr,-.999,.999)*32767).tobytes())

def soundtrack():
    """Original algorithmic score, local voice and designed cues; no sampled music."""
    TMP.mkdir(parents=True,exist_ok=True);sr=48000;n=sr*DURATION
    music=np.zeros((n,2),np.float32);voice=np.zeros(n,np.float32);duck=np.ones(n,np.float32)
    rng=np.random.default_rng(20261025)
    def add(at,data,gain=.1,pan=0):
        a=int(at*sr);data=np.asarray(data,np.float32)
        b=min(n,a+len(data));size=b-a
        if size>0:music[a:b,0]+=data[:size]*gain*(1-pan*.35);music[a:b,1]+=data[:size]*gain*(1+pan*.35)
    bpm=92;beat=60/bpm;bar=beat*4
    chords=[(50,57,60,65),(46,53,58,62),(53,60,65,69),(48,55,60,64)]
    for k,start in enumerate(np.arange(0,DURATION,bar)):
        notes=chords[k%4];length=bar*1.75;t=np.arange(int(length*sr))/sr
        env=np.minimum(1,t/.65)*np.minimum(1,(length-t)/1.6)
        pad=np.zeros_like(t)
        for j,midi in enumerate(notes):
            hz=440*2**((midi-69)/12)
            pad+=(np.sin(2*np.pi*hz*t)+.3*np.sin(2*np.pi*(hz*1.002)*t)+.12*np.sin(2*np.pi*2*hz*t))/(len(notes)*1.42)
        add(start,pad*env,.10,.4*math.sin(k))
        # Soft marimba-like arpeggio, widening the stereo field.
        for j in range(8):
            st=start+j*beat/2
            if st<8 or st>153:continue
            note=notes[(j+k)%4]+12;hz=440*2**((note-69)/12)
            tt=np.arange(int(.65*sr))/sr
            sig=(np.sin(2*np.pi*hz*tt)+.16*np.sin(2*np.pi*3*hz*tt))*np.exp(-tt*7)*np.minimum(tt/.008,1)
            add(st,sig,.033,(-1)**j*.7)
    for k,st in enumerate(np.arange(16,DURATION-4,beat)):
        if k%2==0:
            tt=np.arange(int(.32*sr))/sr
            kick=np.sin(2*np.pi*(47*tt+18*(1-np.exp(-tt*18))/18))*np.exp(-tt*16)*np.minimum(1,tt/.003)
            add(st,kick,.055)
        tt=np.arange(int(.07*sr))/sr
        noise=rng.normal(0,1,len(tt));noise=np.r_[0,np.diff(noise)]
        add(st+beat/2,noise*np.exp(-tt*85)*np.minimum(1,tt/.002),.006,(-1)**k*.5)
    # A restrained transition swell and paired UI tones at each chapter.
    for _,at,_ in TIMELINE[1:]:
        tt=np.arange(sr)/sr;noise=rng.normal(0,1,sr)
        noise=np.convolve(noise,np.ones(19)/19,'same')
        add(at-.6,noise*np.sin(np.pi*tt)**2,.06,-.3)
        tt=np.arange(int(.34*sr))/sr
        add(at+.14,(np.sin(2*np.pi*880*tt)+.5*np.sin(2*np.pi*1320*tt))*np.exp(-tt*15)*np.minimum(tt/.006,1),.035,.3)
    # Rotor texture follows recorded motor duty and the exact replay mapping.
    for p,start,end in [s for s in TIMELINE if s[0] in ('blue','red','turns','left')]:
        r=FlightRecord(RECORDS/p)
        wall=np.arange(int((end-start)*sr))/sr
        sim=16+np.maximum(0,wall-1.2)*2
        duties=np.mean([q['motor_duty'] for q in r.rows],axis=1)
        duty=np.interp(sim,r.times,duties)
        phase=2*np.pi*np.cumsum(90+65*duty)/sr
        rotor=(np.sin(phase)+.2*np.sin(phase*4.03)+.1*np.sin(phase*6.02))*duty
        add(start,rotor,.018,-.4)
    plan=json.loads((TMP/'narration_plan.json').read_text(encoding='utf8'))
    for v in plan:
        a=wave_read(TMP/v['file']);original=len(a)/sr
        # Mild deterministic time fitting is restricted to voice, never flights.
        if original>v['max_s']:
            rate=original/v['max_s']
            if rate>1.32:raise ValueError(f'Voice {v["index"]} needs rewriting, ratio {rate}')
            fitted=TMP/f'voice_{v["index"]:02}_fit.wav'
            subprocess.run(['ffmpeg','-v','error','-y','-i',str(TMP/v['file']),'-af',f'atempo={rate:.7f}',str(fitted)],check=True)
            a=wave_read(fitted)
        peak=float(np.max(np.abs(a)));a=a*(.66/max(.01,peak))
        at=int(v['start']*sr);voice[at:at+len(a)]+=a
        # A soft attack/release duck, never abrupt pumping under the narration.
        left=max(0,at-int(.25*sr));right=min(n,at+len(a)+int(.4*sr))
        env=np.ones(right-left,np.float32)*.42
        ramp=min(int(.25*sr),len(env));env[:ramp]=np.linspace(1,.42,ramp)
        ramp=min(int(.4*sr),len(env));env[-ramp:]=np.linspace(.42,1,ramp)
        duck[left:right]=np.minimum(duck[left:right],env)
        v['duration_s']=len(a)/sr;v['original_duration_s']=original
    music*=duck[:,None]
    master=music+voice[:,None]
    fade=np.ones(n,np.float32);fade[:sr]=np.linspace(0,1,sr);fade[-2*sr:]=np.linspace(1,0,2*sr)
    master*=fade[:,None]
    peak=float(np.max(np.abs(master)))
    if peak>.89:master*=.89/peak
    wave_write(TMP/'soundtrack.wav',master)
    (TMP/'voice_manifest.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
    report=dict(duration_s=DURATION,sample_rate=sr,channels=2,voice='Microsoft Haruka Desktop, local SAPI',
                music='Original deterministic synthesis, seed 20261025; no samples or external services',
                rotor='Designed audio texture follows recorded mean motor duty; not a real microphone recording',
                peak_dbfs=float(20*np.log10(np.max(np.abs(master)))),clipped_samples=int(np.count_nonzero(np.abs(master)>=1)),
                voice_clips=len(plan),all_voices_fit=all(v['duration_s']<=v['max_s']+.1 for v in plan))
    (TMP/'audio_review.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2),flush=True)

def previews(times):
    prod=Production()
    try:
        files=[]
        for t in times:
            f=TMP/f'preview_{t:06.2f}.jpg';prod.frame(t).save(f,quality=95);files.append(f)
        for k in range(0,len(files),6):
            subset=files[k:k+6];sheet=Image.new('RGB',(1440,3*432),BG)
            for j,file in enumerate(subset):
                tile=Image.open(file).resize((720,405));x=(j%2)*720;y=(j//2)*432
                sheet.paste(tile,(x,y));txt(sheet,(x+12,y+405),file.stem,16,MUTED,'en')
            sheet.save(TMP/f'contact_{k//6:02}.jpg',quality=94)
        print(json.dumps(dict(previews=[str(f) for f in files]),indent=2),flush=True)
    finally:prod.close()

def make_video(args):
    prod=Production();output=OUT/'rescue_drone_premium_silent.mp4'
    if output.exists() and not args.overwrite:raise FileExistsError(output)
    for name,count in [('opening',240),('closing',390)]:
        if not all((TMP/name/f'{i:04}.jpg').is_file() for i in range(count)):
            raise FileNotFoundError(f'Complete the {name} studio animation first')
    starttime=__import__('time').monotonic()
    try:
        with imageio.get_writer(output,fps=FPS,codec='libx264',macro_block_size=1,
                                ffmpeg_params=['-crf','17','-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart'],ffmpeg_log_level='error') as writer:
            for frame in range(DURATION*FPS):
                writer.append_data(np.asarray(prod.frame(frame/FPS)))
                if frame%(FPS*5)==0:
                    elapsed=__import__('time').monotonic()-starttime
                    print(json.dumps(dict(frame=frame,total=DURATION*FPS,seconds=frame/FPS,elapsed_s=round(elapsed,1),fps=round((frame+1)/max(.1,elapsed),1))),flush=True)
        evidence={}
        for p,r in prod.records.items():
            evidence[p]={name:sha(RECORDS/p/name) for name in ['trace.jsonl','physical_score.json','vla_link_events.json']}
        report=dict(output='rescue_drone_premium.mp4',frames=DURATION*FPS,fps=FPS,duration_s=DURATION,width=W,height=H,
                    source_records=str(RECORDS.relative_to(ROOT)),checkpoint_sha256=CHECKPOINT,
                    same_final_model=True,physical_replay_only=True,real_flight=False,
                    continuous_flights=[dict(profile=p,video_start_s=s+1.2,sim_start_s=16,sim_end_s=float(prod.records[p].times[-1]),speed=2,omitted_middle_s=0) for p,s,e in TIMELINE if p in prod.records],
                    sections=[dict(name=n,start_s=s,end_s=e) for n,s,e in TIMELINE],
                    recorded_input_jpegs_verified=len(prod.inputs_verified),input_frames=[dict(profile=p,file=f,sha256=h) for p,f,h in sorted(prod.inputs_verified)],
                    evidence_sha256=evidence,source_sha256={name:sha(ROOT/name) for name in ['make_premium_video.py','render_hero_blender.py','video_production.json']},
                    presentation_only=['Studio mesh illustrations and schematic added sensors','Replay materials, lights, cutaway walls and moving cameras','Path/minimap and graphic overlays','Original synthesized music, local synthesized narration and rotor texture'],
                    limitations=['Known synthetic scene functional checks only','No real flight, payload or wireless validation','No generalization claim'])
        (OUT/'rescue_drone_premium.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        print('PICTURE_RENDER_COMPLETE',flush=True)
    finally:prod.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['plan','audio','preview','render'],required=True)
    parser.add_argument('--times',default='2,10,20,28,33,38,43,49,54,59,69,76,84,93,103,113,121,128,135,142,148,155')
    parser.add_argument('--overwrite',action='store_true');args=parser.parse_args()
    if args.mode=='plan':write_voice_script()
    elif args.mode=='audio':soundtrack()
    elif args.mode=='preview':previews([float(x) for x in args.times.split(',')])
    else:make_video(args)
