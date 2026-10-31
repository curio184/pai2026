"""説明PDF（4ページ）を生成する。本文は 執筆方針.md で合意した文面。

結果の数値は results/rebuild05_summary.json から読む。まだ無ければ〔　〕で空欄にする。
レイアウトの部品は Codex 版（tmp/pdfs/reader_final/generated_source.py）を踏襲した。
"""
import hashlib,json,math,sys
from pathlib import Path
from html import escape
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]          # v11_color
PROJECT=BASE.parent           # drone_rescue_stampfly
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else PROJECT/'output/pdf/説明資料_PAI最終課題_再提出版.pdf'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
SUMMARY=BASE/'results/rebuild05_summary.json'
R=read(SUMMARY) if SUMMARY.exists() else None
BLANK='〔　〕'

pair=read(BASE/'reports/training_diagram01/training_pair.json')
own=np.asarray(pair['state']);action=np.asarray(pair['action_physical_units'])
horizontal_speed=np.linalg.norm(action[:,:2],axis=1)
pair_image=BASE/pair['image_source']['path']
assert hashlib.sha256(pair_image.read_bytes()).hexdigest()==pair['image_source']['sha256']

for name,file in [('JP','BIZ-UDGothicR.ttc'),('JB','BIZ-UDGothicB.ttc')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file,subfontIndex=0))
pdfmetrics.registerFontFamily('JP',normal='JP',bold='JB')
W,H=A4;L=42;CW=W-84
NAVY=colors.HexColor('#102C38');TEAL=colors.HexColor('#087F7F');GRAY=colors.HexColor('#52656D');LIGHT=colors.HexColor('#EEF4F4');LINE=colors.HexColor('#D4DFE1')
BLUE=colors.HexColor('#167CCA');RED=colors.HexColor('#D44946')
OUT.parent.mkdir(parents=True,exist_ok=True)
c=canvas.Canvas(str(OUT),pagesize=A4,pageCompression=1)
c.setTitle('災害救助ドローン');c.setAuthor('');c.setSubject('Physical AI 応用1 最終課題')
page=0;y=0;TOTAL=3

BODY=9.5
def p(text,size=None,bold=False,gap=8,color=NAVY,x=None,width=None,leading=1.6):
    global y
    size=BODY if size is None else size
    x=L if x is None else x;width=CW if width is None else width
    obj=Paragraph(text,ParagraphStyle('p',fontName='JB' if bold else 'JP',fontSize=size,leading=size*leading,textColor=color,wordWrap='CJK'))
    _,h=obj.wrap(width,1000);assert y-h>=46,(page,text[:40],y,h)
    obj.drawOn(c,x,y-h);y-=h+gap
def label(text,gap=7):p(text,11.5,True,gap,TEAL)
def sub(text):p(text,10.3,True,5,NAVY)
def footer():
    c.setStrokeColor(LINE);c.line(L,34,W-L,34);c.setFont('JP',7.5);c.setFillColor(GRAY)
    c.drawString(L,22,'Physical AI 応用1');c.drawRightString(W-L,22,f'{page} / {TOTAL}')
def start(k,title,subtitle,first=False):
    global page,y
    if page:footer();c.showPage()
    page+=1;c.setFillColor(NAVY);c.rect(0,H-144,W,144,fill=1,stroke=0);c.setFillColor(colors.HexColor('#CBA96C'));c.rect(L,H-114,3,79,fill=1,stroke=0)
    y=H-32;p(k,8.5,True,12,colors.HexColor('#A3DDDA'),L+15,CW-15);p(title,28 if first else 23,True,8,colors.white,L+15,CW-15);p(subtitle,10,False,0,colors.HexColor('#DAE7EA'),L+15,CW-15);y=H-165
def table(headers,rows,widths,size=8.8,padding=6,emphasis_first=None,gap=10):
    global y
    def cell(s,h=False,em=False):return Paragraph(escape(str(s)),ParagraphStyle('t',fontName='JB' if h or em else 'JP',fontSize=size,leading=size*1.55,wordWrap='CJK',textColor=colors.white if h else (TEAL if em else NAVY)))
    t=Table([[cell(v,True) for v in headers]]+[[cell(v,em=(emphasis_first is not None and row[0]==emphasis_first)) for v in row] for row in rows],colWidths=widths)
    style=[('BACKGROUND',(0,0),(-1,0),TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[LIGHT,colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),padding),('BOTTOMPADDING',(0,0),(-1,-1),padding)]
    t.setStyle(TableStyle(style))
    _,h=t.wrap(CW,1000);assert y-h>46,(page,'table',y,h);t.drawOn(c,L,y-h);y-=h+gap
def bullets(items,size=8.9,gap=3,last_gap=8):
    for i,s in enumerate(items):p('・'+s,size,gap=last_gap if i==len(items)-1 else gap)

# ---------- 1ページ目 ----------
def diagram():
    """動画の「飛行制御のしくみ」の図をそのまま使う（rescue_drone_final_quad.mp4 の0:26）。"""
    global y
    f=HERE/'figures/video_mechanism.png';iw,ih=Image.open(f).size;hh=CW*ih/iw
    c.drawImage(str(f),L,y-hh,width=CW,height=hh);y-=hh+8

start('PHYSICAL AI','災害救助ドローン','言葉による指示で捜索を任せ、操縦の負担を減らす',True)
label('01  目的と仕組み')
p('災害現場において、人が立ち入りにくい建物を小型ドローンで捜索する。限られた人手で迅速に捜索を進めるため、言葉で任務を伝えると、ドローンが自律的に対象者を探し、確認画像を残す仕組みを制作した。')
p('離陸 → 見回し → 発見確認 → 接近・停止 → 確認画像の保存 → 着陸',9.3,True,9)
p('機体と制御用PCのやり取り',8.2,True,6,TEAL)
diagram()
p('実機は、小型ドローンStampFlyに、カメラと無線通信を担うXIAO ESP32S3 Senseと位置推定用のセンサーを載せ、GPU搭載PCと無線でつなぐ構成を想定している。今回は、この構成（総質量50g）をシミュレーターで再現した。機体の運動はMuJoCoで計算し、カメラ画像はBlenderで描画している。',9.0,gap=10)
label('自律飛行の役割分担')
p('制御プログラムが捜索の手順を進め、SmolVLAが対象者に近づいて止まる動作を決める。',9.2)
table(['担当','役割'],[
 ('制御プログラム','工程ごとに完了を判断して次へ進め、SmolVLAへの指示を切り替える。'),
 ('SmolVLA','画像と指示、機体の状態から、指定された人に近づいて止まるまでの動作を生成する。'),
 ('ArduPilot','VLAの速度指令に従うように、機体の姿勢とモーターを制御する。'),
 ('SSDlite＋色判定','画像から人を検出し、服の色で対象者かどうかを見分ける。3枚続けて見つかれば発見とし、制御プログラムに知らせる。')],[108,CW-108],size=8.7,emphasis_first='SmolVLA')
p('利用者が「青い服の人を探して」と指示すると、制御プログラムがこれを受け取り、「青い服の人に近づいて止まって」のような工程ごとの指示に置き換えてVLAに渡す。VLAへの指示は英語で、現在の画像と機体の状態も一緒に入力する。離陸・旋回・着陸は、通常の制御で行う。',8.5,color=GRAY,gap=0)

# ---------- 2ページ目 ----------
def training_pair_diagram():
    global y
    top=y;box_h=142;input_w=310;gap=22;out_x=L+input_w+gap;out_w=CW-input_w-gap
    c.setFillColor(LIGHT);c.roundRect(L,top-box_h,input_w,box_h,5,fill=1,stroke=0)
    c.setFillColor(colors.HexColor('#F0F5F7'));c.roundRect(out_x,top-box_h,out_w,box_h,5,fill=1,stroke=0)
    c.setFillColor(TEAL);c.setFont('JB',10);c.drawString(L+12,top-19,'入力');c.drawString(out_x+12,top-19,'対応する教師動作')
    c.drawImage(str(pair_image),L+12,top-122,width=112,height=84)
    c.setFont('JP',8);c.setFillColor(GRAY);c.drawString(L+12,top-136,'カメラ画像')
    tx=L+145
    c.setFillColor(NAVY);c.setFont('JB',8.6);c.drawString(tx,top-43,'言葉の指示（日本語訳）')
    c.setFont('JP',9.2);c.drawString(tx,top-60,'青い服の人に');c.drawString(tx,top-75,'近づいて止まって')
    c.setFont('JB',8.6);c.drawString(tx,top-99,'機体の状態')
    c.setFont('JP',8.6);c.drawString(tx,top-115,f'高度 {own[3]:.2f}m');c.drawString(tx,top-130,f'水平速度 {np.linalg.norm(own[:2]):.2f}m/s など')
    cy=top-80;c.setStrokeColor(TEAL);c.setLineWidth(1.2);c.line(L+input_w+3,cy,out_x-3,cy);c.line(out_x-3,cy,out_x-7,cy+3);c.line(out_x-3,cy,out_x-7,cy-3)
    c.setFillColor(GRAY);c.setFont('JP',8);c.drawString(out_x+12,top-36,'水平速度の例（m/s）')
    gx=out_x+32;gy=top-112;gw=out_w-46;gh=62
    c.setStrokeColor(LINE);c.setLineWidth(.5);c.line(gx,gy,gx+gw,gy);c.line(gx,gy,gx,gy+gh)
    c.setFont('JP',7.2);c.setFillColor(GRAY);c.drawRightString(gx-4,gy-2,'0');c.drawRightString(gx-4,gy+gh-2,'0.2');c.drawString(gx,gy-12,'0');c.drawRightString(gx+gw,gy-12,'3.1秒')
    c.setStrokeColor(TEAL);c.setLineWidth(1.5)
    pts=[(gx+i/31*gw,gy+float(v)/.2*gh) for i,v in enumerate(horizontal_speed)]
    path=c.beginPath();path.moveTo(*pts[0])
    for q in pts[1:]:path.lineTo(*q)
    c.drawPath(path,stroke=1,fill=0)
    c.setFillColor(GRAY);c.setFont('JP',7.7);c.drawString(out_x+12,top-136,'アクションチャンク（0.1秒×32ステップ）')
    c.setLineWidth(1);y=top-box_h-10

BODY=8.95
start('LEARNING','飛行動作を学習させる','SmolVLAに、ドローンの飛ばし方を追加で学習させる')
label('02  飛行動作の学習')
p('SmolVLAは、画像と言葉の指示からロボットの動作を生成する公開モデルである。事前学習にはロボットアームのデータが使われており、ドローンの飛行は学習していない。そこで、ドローンの飛び方を追加で学習させた。画像と言葉を理解する部分はそのまま使い、動作を生成する部分だけを学習した。')
sub('教師データの構成')
p('教師データは、入力と出力の組でできている。入力はドローンのカメラ画像、言葉の指示、機体の状態である。出力はその場面で取るべき動作（教師動作）で、前後・左右・上下の速度と旋回の速さを、0.1秒刻みで32ステップ（3.2秒分）並べたものである。これは、SmolVLAが1回の推論で出力するアクションチャンクの形に合わせている。下の図は、実際に使った組の一例である。',gap=6)
training_pair_diagram()
p('この例では、青い服の人に向かって秒速0.2mで進み、止まる位置が近づくと減速する。')
sub('教師動作の作り方')
p('教師動作は、シミュレーター内の人物と機体の位置を使って、プログラムで計算した。人物の手前に止まる位置を決め、そこへ向かう速度を、近づくほど小さくなるように求めた。人物の位置を使うのは教師動作の計算だけで、飛行中のVLAには渡さない。VLAは、カメラ画像から指示された人を見分け、その方向と距離を読み取って動く。')
sub('場面の作り方')
p('同じ場面ばかりで学習すると、VLAは見た目と動作の対応をそのまま覚えてしまう。たとえば人物がいつも同じ場所に立っていれば、「青い服の人」を「部屋の左側にいる人」と覚えても、正しく動けてしまう。そのため、位置を覚えるだけでは正しく動けないように、次の3つを変えた。',gap=6)
table(['変えたもの','内容'],[
 ('人物の配置','同じ部屋の中で、2人の立ち位置を20通りに変えた'),
 ('機体の位置と向き','人物から0.4〜4.0m離れた位置から、さまざまな角度で撮影した'),
 ('服の色','立ち位置はそのままで、2人の服の色を入れ替えた画像を組で用意した')],[108,CW-108],size=8.7,padding=3,gap=7)
p('服の色を入れ替えた組には、青と赤の両方の指示を組み合わせた。人の立ち位置が同じでも、服の色と指示によって向かう相手が変わる。正しく動くには、指示された色と、画像の中の服の色を照らし合わせる必要がある。',gap=4)
p('学習に使った画像は8,408枚で、このうち6,000枚（3,000組）が服の色を入れ替えた組、残りは動画の場面と同じ人物配置の画像である。',gap=0)

# ---------- 3ページ目（現場を想定した試験） ----------
def image_row(items,height=50):
    global y
    gap=14;slot=(CW-gap*(len(items)-1))/len(items)
    for i,(title,path) in enumerate(items):
        x=L+i*(slot+gap);c.setFont('JB',8.4);c.setFillColor(NAVY);c.drawString(x,y-10,title)
        if path is not None and Path(path).exists():
            iw,ih=Image.open(path).size;ww=min(slot,height*iw/ih);hh=ww*ih/iw;c.drawImage(str(path),x+(slot-ww)/2,y-16-hh,width=ww,height=hh)
        else:
            c.setStrokeColor(LINE);c.rect(x,y-16-height,slot,height,stroke=1,fill=0);c.setFont('JP',8);c.setFillColor(GRAY);c.drawCentredString(x+slot/2,y-16-height/2,BLANK)
    y-=height+22

reg={r['id']:r for r in R['video_cases']} if R else {}
H_=R['heldout'] if R else None
PB=R['probe'] if R else None
def note(rid):
    r=reg.get(rid);return Path(r['record'])/'notification.jpg' if r and (Path(r['record'])/'notification.jpg').exists() else None
VIS=['search_fog_light_blue','search_fog_dense_blue','search_dust_blue']
vis_ok=sum(reg[k]['success'] for k in VIS) if R else None
vis_res=(f'3回中{vis_ok}回成功' if vis_ok<3 else '3回中3回成功') if R else BLANK
held_res=f"16回中{H_['total']}回成功" if H_ else BLANK
probe_res=f"64回中{PB['correct']}回、指示した人の方へ向かった" if PB else BLANK

BODY=9.1
start('TEST','現場を想定して試す','通信の遅れや悪い視界の中で、捜索から着陸まで')
label('03  現場を想定した試験')
p('実機での運用を想定し、現場で起こる条件をシミュレーターで再現して試験した。')
sub('通信と推論の遅れ')
p('実機では、機体のカメラ画像を無線で地上のPCへ送り、VLAが生成した動作を機体へ返す。撮影してから動作が機体に届くまでの遅れを0.2秒と想定し、すべての試験に入れた。シミュレーターでは描画と推論の間は物理計算を止め、撮影からちょうど0.2秒後に動作が届くようにした。',gap=4)
p('VLAの動作は書き換えず、そのまま速度指令として使う。アクションチャンクが届いた時点で、最初の2ステップ（0.2秒分）はすでに過ぎているので、3ステップ目から実行し、0.2秒後に次のチャンクへ切り替える。')
sub('現場の条件と結果')
table(['想定した状況','試験の方法','結果'],[
 ('煙や粉じんで視界が悪い','動画と同じ人物配置で、薄い霧・濃い霧・粉じんの中、青い服の人を探す。どれも学習データに含めていない条件',vis_res),
 ('人がどこにいるか分からない','学習に使っていない4つの配置で、青い服の人と赤い服の人を探す。開始位置と向きを変えて各配置4回',held_res),
 ('探す相手が指示で変わる','同じ画像のまま、「青い服の人」「赤い服の人」と指示だけを入れ替える（32枚×2つの指示）',probe_res)],[142,CW-142-118,118],size=8.6,padding=3,gap=8)
image_row([(t,note(rid)) for t,rid in [('通常','search_clear_blue'),('薄い霧','search_fog_light_blue'),('濃い霧','search_fog_dense_blue'),('粉じん','search_dust_blue')]],height=50)
p('各条件で保存した確認画像（VLAに入力したカメラ画像）',7.5,color=GRAY,gap=6)
p('捜索で成功とみなすのは、対象者の発見、接近と停止、確認画像の保存、着陸をすべて終えた場合である。停止は、人物の0.9m手前の目標点から25cm以内で、水平速度0.08m/s以下の状態が3秒以上続いたかで判定した。指示の入れ替えでは、生成した動作の最初の1秒で進む向きが、指示した人の目標点に近ければ正解とした。',gap=4)
p('未学習の4配置は、人物の立ち位置を無作為に決めて試験の前に用意したもので、学習にも開発中の調整にも使っていない。成功の基準も、試験の条件とともに飛行前に決めておいた。',gap=4)
fail_text=''
for cond,rid in [('薄い霧','search_fog_light_blue'),('濃い霧','search_fog_dense_blue'),('粉じん','search_dust_blue')]:
    r=reg.get(rid)
    if r and not r['success']:
        d=r.get('minimum_goal_distance_m');near=f'目標点から{round(d*100):.0f}cmのところまで近づいたが、' if d is not None else ''
        fail_text+=f"{cond}の1回は、{near}止まっていた時間が{r['hold_s']:.1f}秒で、3秒に届かなかった。"
others=[reg.get(k) for k in ['search_clear_blue','search_clear_red','primitive_blue','primitive_red','primitive_turns','primitive_left']]
if R and all(others):
    ok=sum(o['success'] for o in others);tail='すべて成功した。' if ok==6 else f'6回中{ok}回成功した。'
else:tail=BLANK
p(fail_text+'このほか、通常の視界での捜索（青・赤）と、見回しを含まない接近と旋回の飛行は、'+tail,gap=10)
p('検証は1つの部屋と同じ2人に限られ、人物は動かない。飛行はすべてシミュレーターで行い、部品の搭載や電源、無線通信、実機での飛行は検証していない。',gap=8)
p('設定・全記録・出典：<link href="https://github.com/curio184/pai2026" color="#087F7F">github.com/curio184/pai2026</link>（README／docs/THIRD_PARTY.md）',8.1,color=GRAY,gap=0)
footer();c.save()
print(OUT)
