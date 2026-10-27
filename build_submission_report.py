"""Create the current Japanese submission report from frozen experiment records."""
from pathlib import Path
import json,hashlib,os
from html import escape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output/pdf/説明資料_PAI最終課題_提出用.pdf'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
plan=read('tmp/rescue_presentation/plan.json');records=plan['records']
scores={p:read(records+'/'+p+'/physical_score.json') for p in ['blue','red','turns','left']}
assert all(s['success'] for s in scores.values())
data=read('outputs/vla_data_realism_precision_02/manifest.json')
navy=colors.HexColor('#11283a');teal=colors.HexColor('#087f79');muted=colors.HexColor('#526579');pale=colors.HexColor('#edf4f7')
fonts=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
for name,file in [('JP','BIZ-UDGothicR.ttc'),('JBP','BIZ-UDGothicB.ttc')]:pdfmetrics.registerFont(TTFont(name,str(fonts/file),subfontIndex=0))
pdfmetrics.registerFontFamily('JP',normal='JP',bold='JBP')
W,H=A4;LEFT=44;WIDTH=W-88
c=canvas.Canvas(str(OUT),pagesize=A4);c.setTitle('言葉で指示する小型救助ドローン');c.setAuthor('');c.setSubject('Physical AI 応用1 最終課題 / SmolVLA・ArduPilot・MuJoCo')
y=0;page=0
def paragraph(text,size=10.2,bold=False,gap=9,color=navy):
    global y
    p=Paragraph(escape(text).replace('\n','<br/>'),ParagraphStyle('body',fontName='JBP' if bold else 'JP',fontSize=size,leading=size*1.65,textColor=color,wordWrap='CJK'))
    _,h=p.wrap(WIDTH,1000)
    assert y-h>48,(page,text[:35],y,h)
    p.drawOn(c,LEFT,y-h);y-=h+gap
def footer():
    c.setStrokeColor(colors.HexColor('#cbd9e1'));c.line(LEFT,37,W-LEFT,37)
    c.setFont('JP',8);c.setFillColor(muted);c.drawString(LEFT,24,'Physical AI 応用1 / 最終課題 / 2026年10月26日');c.drawRightString(W-LEFT,24,str(page))
def new(title,subtitle):
    global y,page
    if page:footer();c.showPage()
    page+=1;c.setFillColor(teal);c.rect(0,H-10,W,10,fill=1,stroke=0)
    y=H-38;paragraph('RESCUE / VLA',9,bold=True,color=teal,gap=14);paragraph(title,23,bold=True,gap=10);paragraph(subtitle,10,color=muted,gap=16)
def table(headers,rows,widths):
    global y
    def cell(s,head=False):return Paragraph(escape(str(s)),ParagraphStyle('cell',fontName='JBP' if head else 'JP',fontSize=9.1,leading=14.5,wordWrap='CJK',textColor=colors.white if head else navy))
    t=Table([[cell(v,True) for v in headers]]+[[cell(v) for v in row] for row in rows],colWidths=widths)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),teal),('ROWBACKGROUNDS',(0,1),(-1,-1),[pale,colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    _,h=t.wrap(WIDTH,1000);assert y-h>48,(page,h);t.drawOn(c,LEFT,y-h);y-=h+16
def loop_diagram(hardware=False):
    global y
    top=y;boxw=145;xs=[LEFT,LEFT+181,LEFT+362]
    titles=['ドローン','コントローラー','VLA'] if hardware else ['入力','SmolVLA','機体の動作']
    contents=[['カメラ・無線通信','機体側で姿勢を安定化'],['地上PCで受信・送信','画像をVLAへ渡す'],['同じ地上PCで動作','画像と言葉から動作を決定']] if hardware else [['カメラ画像と言葉','高度・速度などの機体情報'],['数秒分の動作を生成','32ステップ × 6成分'],['移動・回転','離陸・着陸']]
    for x,title,lines in zip(xs,titles,contents):
        c.setFillColor(pale);c.roundRect(x,top-90,boxw,90,8,fill=1,stroke=0);c.setFillColor(teal);c.setFont('JBP',11);c.drawString(x+11,top-23,title)
        c.setFont('JP',8.3);c.setFillColor(navy)
        for j,line in enumerate(lines):c.drawString(x+11,top-48-j*17,line)
    def arrow(x1,y1,x2,y2,col):
        c.setStrokeColor(col);c.setFillColor(col);c.setLineWidth(1.5);c.line(x1,y1,x2,y2)
        p=c.beginPath();p.moveTo(x2,y2);p.lineTo(x2-5 if x2>x1 else x2+5,y2+3);p.lineTo(x2-5 if x2>x1 else x2+5,y2-3);p.close();c.drawPath(p,fill=1,stroke=0)
    for i in [0,1]:arrow(xs[i]+boxw,top-40,xs[i+1],top-40,teal)
    if hardware:
        for i in [0,1]:arrow(xs[i+1],top-71,xs[i]+boxw,top-71,colors.HexColor('#ad7437'))
        c.setFont('JP',9);c.setFillColor(muted);c.drawString(LEFT,top-112,'上段：画像・機体情報を送る　　下段：動作・飛行指令を返す')
    else:
        c.setStrokeColor(teal);c.line(xs[2]+72,top-90,xs[2]+72,top-106);c.line(xs[2]+72,top-106,xs[0]+72,top-106);c.line(xs[0]+72,top-106,xs[0]+72,top-90)
        c.setFont('JP',9);c.setFillColor(muted);c.drawString(LEFT+111,top-125,'動いた結果を次の画像で確認し、判断を繰り返す')
    y=top-(137 if not hardware else 127)

new('言葉で指示する小型救助ドローン','カメラ映像と言葉から動作を生成し、指定した人の前まで飛ぶ')
paragraph('1. 目的と、今回取り組んだこと',13,True)
paragraph('災害現場で「青い服の人を探して」と目的を伝えれば、ドローンが対象の人へ近づく。こうした支援を目指し、実在する小型機をもとに、画像と言語を入力とする飛行制御を実装した。今回は被災した建物を想定した一つの室内で、見えている人物への接近と停止を検証した。')
img=ImageReader(str(ROOT/'output/environment/realism/people.png'));iw,ih=img.getSize();height=205;width=height*iw/ih
c.drawImage(img,LEFT+(WIDTH-width)/2,y-height,width,height);y-=height+9
paragraph('図1　実際にVLAへ画像を入力したシミュレーション環境。青と赤の服の人物を同時に配置。',8.4,color=muted,gap=14)
paragraph('2. シミュレーションで実現したタスク',13,True)
paragraph('離陸して空中で静止した後、指定された服の色の人物へ近づき、その前で停止して着陸する。右・左への90度回転と停止も検証した。すべて同じ最終モデルを用い、各飛行を着陸とモーター停止まで完了した。')
paragraph('動画のミッション名は「青い服の人を探して」。モデルへの実際の接近指示は「青い服の人の前で止まって」であり、映像内にも表示している。見えない人物の探索や複数の部屋を巡回する機能は、今回の実装には含めていない。',9.5,color=muted)

new('映像と言葉から、次の動きを決める','VLAによる動作生成と、機体を安定させる飛行制御を組み合わせる')
paragraph('3. システムの構成',13,True);loop_diagram()
table(['役割','実装'],[
['画像・言語からの動作生成','SmolVLA（約4.5億パラメータ）を追加学習。前方RGB画像、指示文、9成分の機体情報を入力する。'],
['出力する動作','前後・左右・上下の速度、回転速度、離陸・着陸の要求を含む6成分。0.1秒間隔で32ステップ分を生成する。'],
['姿勢制御と物理計算','ArduPilotが機体を安定させ、MuJoCoで質量・慣性・モーター・バッテリー・接触を計算する。'],
['カメラ画像と表示','Blenderで同じ室内の前方画像を生成し、実際にVLAへ入力。動画の外部視点は、記録した機体の位置・姿勢から再描画する。']],[112,WIDTH-112])
paragraph('4. 学習方法と工夫',13,True)
paragraph(f'最終段階では{data["images"]:,}枚の画像と{data["samples"]:,}件の教師例を使い、4,000ステップの追加学習を行った。その前に、改訂した室内への外観適応を5,000ステップ実施している。画像には合成した視点と、途中の失敗した飛行から保存したカメラ画像を用いた。')
paragraph('同じ画像・機体情報に対して「青」と「赤」で指示を変えた教師例を用意し、言葉に応じて向かう相手を変えるよう学習させた。人物の立ち姿・衣服・足の接地、床や影も改善し、その画像が入力される環境で改めて飛行を確認した。')
paragraph('人物の座標は教師データ作成と飛行後の評価に使用する。実行中のVLAには渡さず、接近する方向と速度は画像・言葉・機体情報から生成する。',9.4,color=muted)

new('4つの実験で、離陸から着陸まで成功','同じ最終モデル・同じ環境で行った機能確認。未知の環境に対する成功率ではない。')
paragraph('5. 結果',13,True)
table(['実験','記録から確認した結果','判定'],[
['青い服の人への接近',f'人の前で{scores["blue"]["goal_holds"]["blue"]["physical_hold"]["duration_s"]:.2f}秒停止','成功'],
['赤い服の人への接近',f'人の前で{scores["red"]["goal_holds"]["red"]["physical_hold"]["duration_s"]:.2f}秒停止','成功'],
['右90度 → 左90度',f'右{scores["turns"]["rotations"]["right"]["clockwise_rotation_deg"]:.1f}度、左{abs(scores["turns"]["rotations"]["left"]["clockwise_rotation_deg"]):.1f}度で、それぞれ停止','成功'],
['左90度のみ',f'左{abs(scores["left"]["rotations"]["left"]["clockwise_rotation_deg"]):.1f}度で停止','成功']],[145,WIDTH-195,50])
paragraph('停止は、目標点から25cm以内・水平速度0.08m/s以下を3秒以上維持した場合に成功とした。回転は目標角との差10度以内と停止を条件とし、すべての飛行で離陸・空中静止・着陸・モーター停止も確認した。結果は飛行後の物理状態の記録から判定している。')
paragraph('6. 途中の問題と改善',13,True)
paragraph('室内の見た目を変えた直後は、人への接近と停止が安定しなかった。追加学習後も青い服の人の前での停止が短く、停止確認の待ち時間を延ばすだけでは解決しなかった。')
paragraph('教師が目標の25cm手前から速度をゼロにしていたため、わずかな流れに対する補正が不足していた。教師の補正を止める範囲を4cmまで狭め、目標付近でも位置を修正するよう学習した。成功判定の25cm・3秒という条件や姿勢制御器は変更していない。失敗した実行記録も保持している。')
paragraph('7. 結果の範囲',13,True)
paragraph('4回の成功は、固定した室内と指定した指示での機能確認である。別の建物・人物・照明に対する汎化性能は未評価。薄い粉じんは入力画像に含まれるが、濃度を変えた耐性試験はしていない。人物の検出だけでなく移動・回転・着陸までつないだ点を、本課題の成果とする。')
paragraph('最終モデル識別子：'+plan['checkpoint_sha256'][:16]+'…\n実験記録：outputs/ardupilot/realism_precision_03',8.4,color=muted)

new('実在する機体をもとに、実機化を考える','設計案と、今回シミュレーションで確認したことを区別する')
paragraph('8. 実機化の想定構成',13,True);loop_diagram(True)
paragraph('機体はStampFly、カメラと無線通信にはXIAO ESP32S3 Senseを候補とする。地上のGPU搭載PCでVLAを動かし、通信・制御ソフトが画像と機体情報を受信して、VLAが生成した飛行指令を機体へ返す。機体側では姿勢を安定させる制御を続ける。')
paragraph('シミュレーションは追加部品を含む50gの設計想定である。実機を計測して校正した完全な再現モデルではない。搭載重量と推力の余裕、カメラの消費電力、無線の同時動作と遅延、部品の固定方法は未検証であり、実機での飛行や救助活動は行っていない。')
paragraph('9. コードと再現の手順',13,True)
paragraph('提出用コードには、学習・飛行制御・画像生成・採点・動画編集の実装、設定、記録に基づく評価手順を含める。保存した4回の飛行は、VLAの再学習なしで採点し直せる。再学習や新たな飛行にはGPU環境・モデル重み・学習データ・ArduPilotのビルドが別途必要。公開用READMEに、同梱範囲と実行条件を記載する。')
paragraph('10. 主な使用技術・素材',13,True)
for text in [
'SmolVLA / LeRobot：https://huggingface.co/lerobot/smolvla_base （モデルの参照元、Apache-2.0）',
'ArduPilot：https://github.com/ArduPilot/ardupilot （飛行制御、GPL-3.0-or-later）',
'StampFly：https://github.com/M5Fly-kanazawa/stampfly_ecosystem （機体・物理モデルの参照元、MIT）',
'MuJoCo：https://mujoco.org/　／　Blender：https://www.blender.org/',
'MakeHuman：https://www.makehumancommunity.org/　／　Poly Haven：https://polyhaven.com/ （使用した人物・材質素材はCC0）']:
    paragraph(text,8.4,gap=6,color=muted)
paragraph('詳細な参照先と使用バージョンは、コードに添付する素材・ライセンス一覧に記載。フォントファイル、外部モデルの重み、実機ファームウェアのバイナリは再配布しない。',8.5,color=muted)
footer();c.save()
assert page==4
(OUT.with_suffix('.json')).write_text(json.dumps(dict(pages=page,sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(),records=records,checkpoint_sha256=plan['checkpoint_sha256'],account_filename_needs_rename=True,visually_reviewed=False),indent=2),encoding='utf8')
print('SUBMISSION_REPORT_CREATED',OUT)
