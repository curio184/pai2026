"""Japanese presentation cards and explanatory communication animation."""
import math
import numpy as np
from PIL import Image,ImageDraw
import make_premium_video as b

def localize_base(base):
    original=base.txt
    def txt(im,xy,value,size=28,color=base.WHITE,kind='jp',anchor=None):
        if kind=='en' and any('\u3040'<=c<='\u9fff' for c in value):kind='jp'
        return original(im,xy,value,size,color,kind,anchor)
    base.txt=txt
    def footer(im,t,section,mode=''):
        d=ImageDraw.Draw(im);d.line((64,1026,1856,1026),fill=base.LINE,width=1)
        d.line((64,1026,64+int(1792*t/base.DURATION),1026),fill=base.CYAN,width=2)
        txt(im,(64,1040),'RESCUE / VLA',18,base.CYAN,'en')
        labels={'Opening':'災害救助を目指すドローン','The environment':'実験の舞台','How it works':'動く仕組み','Results':'実験結果','Hardware':'実機化の想定構成','Closing':'今後に向けて'}
        label=labels.get(section,'シミュレーションによる実演')
        txt(im,(310,1040),label,18,base.MUTED)
        txt(im,(1856,1040),f'{int(t)//60:02}:{int(t)%60:02}',18,base.MUTED,'en',anchor='ra')
    base.footer=footer

def arrow(im,points,color,progress=None,width=3):
    d=ImageDraw.Draw(im);d.line(points,fill=color,width=width,joint='curve')
    x,y=points[-1];px,py=points[-2];a=math.atan2(y-py,x-px)
    d.polygon([(x,y),(x-14*math.cos(a-.48),y-14*math.sin(a-.48)),(x-14*math.cos(a+.48),y-14*math.sin(a+.48))],fill=color)
    if progress is not None:
        lengths=[math.dist(p,q) for p,q in zip(points,points[1:])];distance=(progress%1)*sum(lengths)
        for p,q,length in zip(points,points[1:],lengths):
            if distance<=length:
                u=distance/length;x=p[0]+u*(q[0]-p[0]);y=p[1]+u*(q[1]-p[1]);d.ellipse((x-7,y-7,x+7,y+7),fill=b.WHITE);break
            distance-=length

def box(im,rect,title,lines,color=b.CYAN,title_size=32):
    b.rounded(im,rect,b.PANEL,b.LINE,20)
    x,y,_,_=rect;b.txt(im,(x+28,y+25),title,title_size,color,'bold')
    for i,line in enumerate(lines):b.txt(im,(x+28,y+83+i*44),line,25,b.WHITE)

class PresentationCards:
    def hero(self,t):
        im=b.shade(b.studio_back('hero',t,1+.045*b.smooth(t/8)))
        b.txt(im,(78,90),'RESCUE / VLA',25,b.CYAN,'en')
        b.txt(im,(73,235),'青い服の人を',80,b.WHITE,'bold')
        b.txt(im,(73,345),'探して。',96,b.WHITE,'bold')
        b.txt(im,(80,540),'言葉で指示する、救助ドローンへ。',33,b.WHITE,'bold')
        b.txt(im,(80,615),'カメラ映像を見て、人に近づく仕組みを作りました。',26,b.MUTED)
        b.txt(im,(80,870),'実在する小型機「StampFly」をもとにしたCG',21,b.MUTED)
        b.txt(im,(80,912),'今回はシミュレーションで検証しています。',23,b.WHITE)
        b.footer(im,t,'Opening');return im

    def world(self,t):
        im=self.image('world_final',min(209,round((t-8)*30))).convert('RGBA')
        alpha=np.broadcast_to((220*np.clip(1-np.arange(1920)/1220,0,1)).astype(np.uint8),(1080,1920))
        overlay=Image.new('RGBA',(1920,1080),(5,13,20,0));overlay.putalpha(Image.fromarray(alpha));im=Image.alpha_composite(im,overlay).convert('RGB')
        b.txt(im,(78,80),'災害現場を想定した室内',25,b.CYAN,'bold')
        b.txt(im,(73,195),'服の色を見分けて、',61,b.WHITE,'bold')
        b.txt(im,(73,288),'その人の前へ。',70,b.WHITE,'bold')
        b.txt(im,(80,450),'「青い服の人を探して」',31,b.BLUE,'bold')
        b.txt(im,(80,510),'「赤い服の人を探して」',31,b.RED,'bold')
        b.txt(im,(80,660),'人物を見分け、近づいて停止する実験です。',25,b.WHITE)
        b.txt(im,(80,865),'この部屋のカメラ映像を使って飛行します。',27,b.WHITE,'bold')
        b.txt(im,(80,914),'今回は、カメラに見えている人を対象にしています。',23,b.MUTED)
        b.footer(im,t,'The environment');return im

    def architecture(self,t):
        im=b.base().copy();u=t-15
        b.txt(im,(75,78),'動く仕組み',25,b.CYAN,'bold')
        b.txt(im,(70,150),'映像と言葉から、次の動きを決めます',56,b.WHITE,'bold')
        box(im,(80,325,560,720),'① 映像と指示',['前方カメラの画像','「青い服の人の前で止まって」','高度や速度などの機体情報'],title_size=33)
        box(im,(735,325,1215,720),'② VLAが判断',['画像と言葉をもとに','数秒分の動作をまとめて生成','使用モデル：SmolVLA'],title_size=33)
        box(im,(1390,325,1840,720),'③ 機体が動く',['前後・左右・上下に移動','左右に回転','離陸・着陸'],title_size=33)
        arrow(im,[(560,525),(735,525)],b.CYAN,u/2)
        arrow(im,[(1215,525),(1390,525)],b.CYAN,u/2-.4)
        b.txt(im,(108,645),'映像を見て、繰り返し判断',24,b.MUTED)
        arrow(im,[(1615,720),(1615,795),(320,795),(320,720)],b.GOLD,u/4)
        b.txt(im,(740,815),'動いた結果を、次の画像で確認',27,b.GOLD)
        b.txt(im,(82,905),'ArduPilotで姿勢を安定させ、MuJoCoで機体の動きを計算します。',28,b.WHITE)
        b.footer(im,t,'How it works');return im

    def hardware(self,t):
        start=next(s for n,s,e in b.TIMELINE if n=='hardware');u=t-start
        im=b.base().copy();b.txt(im,(75,78),'実機化の想定構成',25,b.CYAN,'bold')
        b.txt(im,(70,145),'機体と地上PCを、無線でつなぎます',55,b.WHITE,'bold')
        b.rounded(im,(80,290,635,825),b.PANEL,b.LINE,22)
        b.txt(im,(110,315),'ドローン：StampFly',34,b.WHITE,'bold')
        d=ImageDraw.Draw(im)
        for x,y in [(205,450),(475,450),(205,590),(475,590)]:
            d.line((340,520,x,y),fill=b.MUTED,width=12);d.ellipse((x-52,y-32,x+52,y+32),outline=b.CYAN,width=4)
        d.rounded_rectangle((280,470,400,570),radius=16,fill='#153d40',outline=b.CYAN,width=3)
        d.ellipse((321,485,359,523),fill='#07121d',outline=b.WHITE,width=2)
        b.txt(im,(111,670),'カメラ・無線通信',29,b.WHITE,'bold')
        b.txt(im,(111,722),'機体側で姿勢を安定させる',25,b.MUTED)
        b.rounded(im,(970,290,1840,825),'#0a1c2a',b.LINE,22)
        b.txt(im,(1000,315),'地上PC',35,b.WHITE,'bold')
        box(im,(1020,455,1350,700),'コントローラー',['映像・状態を受信','飛行指令を送信'],title_size=28)
        box(im,(1480,455,1800,700),'VLA',['画像と言葉から','アクションを生成'],title_size=32)
        b.txt(im,(1455,365),'「青い服の人を探して」',24,b.WHITE,'bold')
        arrow(im,[(1630,405),(1630,455)],b.CYAN,u/3)
        arrow(im,[(635,445),(875,445),(875,520),(1020,520)],b.CYAN,u/4)
        b.txt(im,(665,370),'カメラ映像',26,b.CYAN,'bold');b.txt(im,(665,408),'機体の状態',26,b.CYAN,'bold')
        arrow(im,[(1020,645),(810,645),(810,715),(635,715)],b.GOLD,u/4-.5)
        b.txt(im,(665,750),'飛行指令',26,b.GOLD,'bold')
        arrow(im,[(1350,520),(1480,520)],b.CYAN,u/2);b.txt(im,(1360,475),'画像など',20,b.CYAN)
        arrow(im,[(1480,645),(1350,645)],b.GOLD,u/2-.5);b.txt(im,(1358,665),'動作指令',20,b.GOLD)
        b.txt(im,(1000,755),'コントローラーとVLAは、同じPC上のソフトです。',24,b.MUTED)
        b.txt(im,(85,865),'カメラ・無線の候補：XIAO ESP32S3 Sense　／　計算処理：地上のGPU搭載PC',23,b.WHITE)
        b.txt(im,(85,912),'実機への搭載、電源、無線通信は未検証です。',25,b.MUTED)
        b.footer(im,t,'Hardware');return im

    def outro(self,t):
        start=next(s for n,s,e in b.TIMELINE if n=='outro');u=t-start
        im=b.shade(b.studio_back('detail',145+u))
        b.txt(im,(78,80),'RESCUE / VLA',25,b.CYAN,'en')
        b.txt(im,(73,220),'操縦から、',78,b.WHITE,'bold')
        b.txt(im,(73,330),'言葉での指示へ。',74,b.WHITE,'bold')
        b.txt(im,(80,535),'災害救助に向けた、最初の一歩。',34,b.WHITE,'bold')
        b.rounded(im,(75,695,1225,930),'#081724',b.LINE,18)
        b.txt(im,(100,720),'今回できたこと',27,b.CYAN,'bold')
        b.txt(im,(100,770),'見えている人への接近・停止と、離陸・回転・着陸。',26,b.WHITE)
        b.txt(im,(100,822),'見えない人の探索や、実機での飛行は今後の課題です。',25,b.MUTED)
        b.txt(im,(100,878),'人物・背景素材：MakeHuman / Poly Haven（CC0）',21,b.MUTED)
        b.footer(im,t,'Closing');return im
