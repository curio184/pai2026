"""Four-page review PDF. Run only after the skill artifact marker and completed evidence."""
import json,hashlib
from pathlib import Path
from html import escape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle
from PIL import Image
from pypdf import PdfReader
from training_history import lineage
BASE=Path(__file__).resolve().parents[1];PROJECT=BASE.parent;ROOT=Path('C:/Temp/pai2026_submission/pai2026')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
report=read(BASE/'results/all_trials.json');selected=read(BASE/'protocol/selected_final.json');probe=read(BASE/'probe/outputs/summary.json')
assert report['preregistered_goal_met'],'Completion claim requires the frozen acceptance gate'
train=read(BASE/'models'/selected['candidate']/'result.json');started=read(BASE/'models'/selected['candidate']/'started.json')
history=lineage(BASE,selected['candidate']);step_text='＋'.join(f"{h['steps']:,}" for h in history)
assert (BASE/'figures/probe_01.png').exists()
OUT=BASE/'reports/output/pdf/説明資料_PAI最終課題_v1.1_検証更新版.pdf';OUT.parent.mkdir(parents=True,exist_ok=True)
for name,file in [('JP','BIZ-UDGothicR.ttc'),('JB','BIZ-UDGothicB.ttc')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file,subfontIndex=0))
pdfmetrics.registerFontFamily('JP',normal='JP',bold='JB')
W,H=A4;L=42;CW=W-84;NAVY=colors.HexColor('#102C38');TEAL=colors.HexColor('#087F7F');GRAY=colors.HexColor('#52656D');LIGHT=colors.HexColor('#EEF4F4');LINE=colors.HexColor('#D4DFE1')
c=canvas.Canvas(str(OUT),pagesize=A4,pageCompression=1);c.setTitle('災害救助ドローン / v1.1 検証更新版');c.setAuthor('');c.setSubject('Physical AI 応用1 最終課題');page=0;y=0
def p(text,size=9.5,bold=False,gap=8,color=NAVY,x=None,width=None):
    global y
    x=L if x is None else x;width=CW if width is None else width
    obj=Paragraph(text,ParagraphStyle('p',fontName='JB' if bold else 'JP',fontSize=size,leading=size*1.6,textColor=color,wordWrap='CJK'))
    _,h=obj.wrap(width,1000);assert y-h>=46,(page,text[:40],y,h)
    obj.drawOn(c,x,y-h);y-=h+gap
def label(text):p(text,11.5,True,7,TEAL)
def footer():
    c.setStrokeColor(LINE);c.line(L,34,W-L,34);c.setFont('JP',7.5);c.setFillColor(GRAY)
    c.drawString(L,22,'Physical AI 応用1 / 最終課題・v1.1 検証更新版');c.drawRightString(W-L,22,f'{page} / 4')
def start(k,title,sub,first=False):
    global page,y
    if page:footer();c.showPage()
    page+=1;c.setFillColor(NAVY);c.rect(0,H-144,W,144,fill=1,stroke=0);c.setFillColor(colors.HexColor('#CBA96C'));c.rect(L,H-114,3,79,fill=1,stroke=0)
    y=H-32;p(k,8.5,True,12,colors.HexColor('#A3DDDA'),L+15,CW-15);p(title,28 if first else 23,True,8,colors.white,L+15,CW-15);p(sub,10,False,0,colors.HexColor('#DAE7EA'),L+15,CW-15);y=H-165
def table(headers,rows,widths,size=8.8):
    global y
    def cell(s,h=False):return Paragraph(escape(str(s)),ParagraphStyle('t',fontName='JB' if h else 'JP',fontSize=size,leading=size*1.55,wordWrap='CJK',textColor=colors.white if h else NAVY))
    t=Table([[cell(v,True) for v in headers]]+[[cell(v) for v in row] for row in rows],colWidths=widths)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[LIGHT,colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    _,h=t.wrap(CW,1000);assert y-h>46,(page,'table',y,h);t.drawOn(c,L,y-h);y-=h+10
def image(path,width=CW):
    global y
    iw,ih=Image.open(path).size;hh=width*ih/iw;assert y-hh>=46
    c.drawImage(str(path),L+(CW-width)/2,y-hh,width=width,height=hh);y-=hh+8
def image_row(items,height=82):
    global y
    gap=14;slot=(CW-gap*(len(items)-1))/len(items)
    for i,(title,path) in enumerate(items):
        x=L+i*(slot+gap);c.setFont('JB',8.8);c.setFillColor(NAVY);c.drawString(x,y-11,title)
        iw,ih=Image.open(path).size;ww=min(slot,height*iw/ih);hh=ww*ih/iw;c.drawImage(str(path),x+(slot-ww)/2,y-22-hh,width=ww,height=hh)
    y-=height+32
def stat(v,g='all',key=None):return next(s for s in report['heldout_statistics'] if s['model']==v and s['group']==g and s['key']==key)
def ps(v,g='runtime_bilingual'):return next(s for s in probe['summary'] if s['model']==v and s['prompt_group']==g)
def count(s):return f"{s['k']} / {s['n']}"
def diagram():
    global y
    top=y;gap=20;bw=(CW-2*gap)/3
    for i,(head,lines) in enumerate([('入力',['画像・工程の指示','機体の状態']),('SmolVLA',['次の動作列を生成','移動・旋回・離着陸']),('飛行と物理計算',['ArduPilot：姿勢制御','MuJoCo：物理状態を更新'])]):
        x=L+i*(bw+gap);c.setFillColor(LIGHT);c.roundRect(x,top-77,bw,77,6,stroke=0,fill=1);c.setFillColor(TEAL);c.setFont('JB',10.5);c.drawString(x+10,top-22,head);c.setFont('JP',8.2);c.setFillColor(NAVY)
        for j,line in enumerate(lines):c.drawString(x+10,top-44-j*15,line)
        if i<2:
            c.setStrokeColor(TEAL);c.line(x+bw+3,top-39,x+bw+gap-3,top-39);c.line(x+bw+gap-3,top-39,x+bw+gap-7,top-36);c.line(x+bw+gap-3,top-39,x+bw+gap-7,top-42)
    y=top-85;p('Blenderが更新後の位置・姿勢から次のカメラ画像を描画する',8.2,color=GRAY,gap=12)

start('PHYSICAL AI','災害救助ドローン','言葉による指示で捜索を任せ、操縦の負担を減らす',True)
label('01  目的と仕組み')
p('人が立ち入りにくい建物を、小型ドローンで捜索する。機体ごとに人が操縦する負担を減らすため、言葉で任務を伝え、対象者を探して確認画像を残す仕組みを制作した。被災した建物を想定した1室で、一連の動作を実装・検証した。')
p('離陸 → 見回し → 発見確認 → 接近・停止 → 確認画像の保存 → 着陸',9.3,True,12)
diagram()
label('役割を分け、判断を別の仕組みで確認する')
table(['担当','役割'],[
    ('任務管理','工程の順序・完了判定、再旋回・再捕捉・時間切れを管理'),
    ('SSDlite＋色判定','人物と服の色を判定し、連続3画像で「発見」を確認'),
    ('SmolVLA','画像・工程の指示・機体状態から、速度・旋回・離着陸要求の6成分を生成'),
    ('変換＋ArduPilot','速度から姿勢目標へ変換して姿勢を安定化。水平速度0.2m/s、旋回速度0.35rad/sを上限とする')],[108,CW-108])
p('今回のVLAには過去の画像列や任務履歴を入力しない。現在の画像に現れない工程の進み具合は任務管理が持ち、人物の発見は独立した検出器で確認する。動作生成と確認を分離したが、誤りを必ず防げるという保証ではない。',9.2)
p('上位の「青い服の人を探して」はVLAへ直接渡さず、「青い服の人の前で止まって」などの工程指示に切り替える。本番の入力は英日併記。任意の文章から捜索手順を計画する機能ではない。',8.6,color=GRAY,gap=0)

start('IMPLEMENTATION','飛行制御への追加学習','位置と色の結び付きを崩し、指定した相手を選ぶ動作を学習')
label('02  ドローンに合わせた動作と教師データ')
p('事前学習済みのSmolVLAを用い、画像や指示、機体の状態と飛行動作を対応付けた。動画のv1.0に加え、配置変更で見つかった弱点を直すため、別のモデルv1.1を追加学習した。')
table(['項目','内容'],[
    ('入力と動作','320×240 RGB画像、工程指示、9成分の機体状態。6成分の動作を32ステップ分生成'),
    ('v1.0','外観適応5,000ステップ＋停止改善4,000ステップ。最終段階は2,408画像・19,224教師例'),
    ('v1.1のデータ','20配置・4,000枚を新規生成。同じ人物・位置・視点のまま服色を交換した2,000組。既存の2,408枚も保持'),
    ('学習の組み方','同じ画像で青・赤の指示を交換する組と、服色を交換する組を学習。接近時の一人だけが見える画像も含む'),
    ('更新する部分',f"画像エンコーダーを固定し、動作生成部とテキスト層の一部を更新。追加学習は{step_text}ステップ、各段階の最終重みを使用")],[91,CW-91])
p('最初の候補は開発試験4/8成功。目標付近と従来配置の例を増やし、速度0.26m/sまでの状態を追加して7/8成功となった。残る着陸中の接近に備え、教師の停止位置を10cm手前へ移した。採点点・基準・制御器は変更せず、開発試験の画像は学習していない。',8.4,color=GRAY,gap=8)
label('停止精度を改善した経緯')
p('外観適応前後の停止時間（青／赤）は0.00／0.00秒→2.97／3.07秒。教師が補正を止める範囲を25cmから4cmへ狭めた停止改善では、2.63／3.87秒→5.75／4.67秒となった。',9.2,gap=5)
p('前者では描画版、後者では工程判定も変更したため、追加学習だけの効果ではない。今回のv1.0対v1.1は制御器を固定して比較した。各数値の元記録はREADMEから参照できる。',8.5,color=GRAY)
label('実行中に正解の座標を渡さない')
p('人物の正解座標や目標までの正解距離は、実行中のVLA・人物判定・任務管理へ渡さない。真値は教師データの作成、描画・センサー合成と飛行後の採点に限って利用する。入力画像・動作列・機体状態・工程を保存し、全実行を記録で追えるようにした。',9.2)
p('停止の判定は目標点から25cm以内、水平速度0.08m/s以下を3秒以上。その他の既存判定も維持し、結果を見て基準を緩めていない。',8.6,color=GRAY,gap=0)

start('RESULTS / VIDEO v1.0','発見から着陸までを確認','公開済み動画はv1.0の記録。映像は変更せず、追加検証を次頁に示す')
label('03  動画で示した結果と実機への展開')
image_row([(name,ROOT/f'rescue_search/runs/eval03/{condition}_blue/notification.jpg') for name,condition in [('通常','clear'),('薄い霧','fog_light'),('濃い霧','fog_dense'),('粉じん','dust')]])
p('実際のモデル入力に由来する確認画像。外部視点の動画は記録した位置・姿勢から再描画し、VLA入力欄には保存した原JPEGを表示した。',8.3,color=GRAY,gap=10)
cases=[('青い服','通常','eval03/clear_blue','blue'),('青い服','薄い霧','eval03/fog_light_blue','blue'),('青い服','濃い霧','eval03/fog_dense_blue','blue'),('青い服','粉じん','eval03/dust_blue','blue'),('赤い服','通常','eval_red01/clear_red','red')]
rows=[]
for target,condition,key,color in cases:
    s=read(ROOT/'rescue_search/runs'/key/'search_score.json');assert s['success'];rows.append((target,condition,'完了',f"{s['physical']['goal_holds'][color]['physical_hold']['duration_s']:.2f}秒"))
table(['対象','視界条件','v1.0の捜索','停止の継続時間'],rows,[80,100,160,CW-340])
p('v1.0の表は1室・固定配置で各条件1回の最終確認。完了は発見、接近・停止、画像保存、着陸・モーター停止を含む。一般的な成功率を示す統計ではない。',8.8)
label('v1.1でも動画の動作を確認')
p('青・赤への接近、右→左と左だけの旋回、通常視界の青・赤の捜索、薄い霧・濃い霧・粉じんでの捜索の計9件を確認した（9/9成功）。動画と新しい検証のモデルを区別し、両者の記録を残している。',9.2)
p('今回の学習用描画濃度0.004に対し、霧・粉じんの評価値は0.06／0.12。描画パラメーターとして15～30倍であり、実際の視程や粒子濃度の倍率ではない。発見は検出器が担い、VLAはその視界下での接近・停止などを生成する。',8.8)
label('実機での飛行は未検証')
p('実在するStampFlyとカメラ、制御用PCを組み合わせ、映像と飛行指令を無線で送受信する構成を検討した。今回は総質量50gの設計条件でのシミュレーションであり、搭載・電源・通信・実機飛行の成立を実測確認したものではない。',9.2,gap=0)

start('VALIDATION / v1.1','配置を変えて、色の選択を検証','弱点の発見 → 学習データの見直し → 未学習配置での同条件比較')
label('04  位置への依存を調べる')
p('v1.0は配置交換で対象を見失い、青の目標点から1.218mのまま、元の青の位置にある赤の目標点へ0.204mまで接近した。位置への依存が疑われた。データの対応を崩して学習し直し、v1.1はこの既知の失敗配置でも完了した（1回）。',9.2)
p('学習20配置、開発確認2配置、最終評価4配置を分離。最終評価は4配置×青・赤×2初期条件の16試験／モデル。位置±5cm・向き±5度の乱数と成功条件を事前記録し、両モデルに同じ条件を与えた。失敗も全件含めた。',8.8)
table(['最終評価','v1.0','v1.1'],[(label,count(stat('v1.0',g,k)),count(stat('v1.1',g,k))) for g,k,label in [('all',None,'全試験'),('color','blue','青い服への指示'),('color','red','赤い服への指示')]],[CW-180,90,90],size=9)
s=stat('v1.1');p(f"参考：独立性を仮定したv1.1の95% Wilson区間は{s['wilson95'][0]*100:.1f}～{s['wilson95'][1]*100:.1f}%。同じ部屋の関連した少数試験であり、任意の環境での信頼性を表さない。",8.3,color=GRAY,gap=9)
image(BASE/'figures/probe_01.png')
a,b=ps('v1.0'),ps('v1.1');j=ps('v1.1','japanese')
p(f"固定した32画像で青・赤の指示を交換。指定目標の方向により近い出力は、本番の英日併記でv1.0 {a['correct_goal']}/{a['outputs']}、v1.1 {b['correct_goal']}/{b['outputs']}。服色交換と指示交換の4通りすべて正解はv1.1 {b['whole_quartet_correct']}/{b['quartets']}組。日本語のみは{j['correct_goal']}/{j['outputs']}。",8.7,gap=7)
p('図は事前指定した服色交換例。矢印は先頭10ステップの水平速度平均の向きで、飛行軌跡ではない。静止・同点は不正解。画像の組は互いに関連し、飛行成功率とは別の検査である。',8.1,color=GRAY,gap=8)
p('検証範囲は同じ部屋・同じ2人の外見・静止人物・限定した配置範囲。未知の部屋、移動する人物、複数室は未検証。VLAは動作生成を担い、工程管理と発見確認は別の仕組みが担う。',8.5,gap=8)
p('<link href="https://github.com/curio184/pai2026" color="#087F7F">github.com/curio184/pai2026</link>：READMEに事前条件・全実行・学習記録・モデルSHAを掲載。出典：SmolVLA / LeRobot、ArduPilot、MuJoCo、Blender、SSDlite、StampFly ecosystem、MakeHuman、Poly Haven（docs/THIRD_PARTY.md）。',8,color=GRAY,gap=0)
footer();c.save();reader=PdfReader(str(OUT));assert len(reader.pages)==4
full='\n'.join(p.extract_text() for p in reader.pages);(BASE/'reports/report_extracted.txt').write_text(full,encoding='utf-8')
assert all(t in full for t in ['v1.0','v1.1','未検証','連続3画像','0.08','16'])
(BASE/'reports/pdf_check.json').write_text(json.dumps(dict(pages=4,pdf_sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(),original_pdf_modified=False,visually_reviewed=False,selected_checkpoint_sha256=selected['checkpoint_sha256']),indent=2))
print(OUT)
