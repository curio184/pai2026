"""Four-page review PDF. Run only after the skill artifact marker and completed evidence."""
import json,hashlib,argparse
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
from navfocus_labels import LABELS
BASE=Path(__file__).resolve().parents[1];PROJECT=BASE.parent;ROOT=Path('<WORK_ROOT>/repository')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
parser=argparse.ArgumentParser();parser.add_argument('--review-incomplete',action='store_true');args=parser.parse_args()
report=read(BASE/'results/all_trials_receipt.json');selected=read(BASE/'protocol/selected_navfocus.json');probe=read(BASE/'probe_navfocus/outputs/summary.json')
assert report['completed']==42 and report['all_new_records_independently_rescored'] and report['probe_arithmetic_and_images_verified']
assert report['preregistered_goal_met'] or args.review_incomplete,'Completion claim requires the frozen acceptance gate'
review=not report['preregistered_goal_met']
assert selected['candidate']=='train16_en','Review the narrative for any later training recipe'
train=read(BASE/'models'/selected['candidate']/'result.json');started=read(BASE/'models'/selected['candidate']/'started.json')
visibility=read(BASE/'reports/v11_training_visibility_train16.json')
assert visibility['verified'] and visibility['dataset_audit_sha256']==started['dataset_audit_sha256']
final_completion=read(BASE/'reports/train16_final_checkpoint_completion_audit.json')
assert final_completion['passed'] and final_completion['final_sha256']==selected['checkpoint_sha256']
history=lineage(BASE,selected['candidate']);step_text='＋'.join(f"{h['steps']:,}" for h in history)
assert (BASE/'figures_navfocus/probe_01.png').exists()
OUT=BASE/('reports/output/pdf/説明資料_PAI最終課題_v1.1_検証レビュー.pdf' if review else 'reports/output/pdf/説明資料_PAI最終課題_v1.1_検証更新版.pdf');OUT.parent.mkdir(parents=True,exist_ok=True)
for name,file in [('JP','BIZ-UDGothicR.ttc'),('JB','BIZ-UDGothicB.ttc')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file,subfontIndex=0))
pdfmetrics.registerFontFamily('JP',normal='JP',bold='JB')
W,H=A4;L=42;CW=W-84;NAVY=colors.HexColor('#102C38');TEAL=colors.HexColor('#087F7F');GRAY=colors.HexColor('#52656D');LIGHT=colors.HexColor('#EEF4F4');LINE=colors.HexColor('#D4DFE1')
c=canvas.Canvas(str(OUT),pagesize=A4,pageCompression=1);c.setTitle('災害救助ドローン / v1.1 '+('固定検証レビュー・合格条件未達' if review else '検証更新版'));c.setAuthor('');c.setSubject('Physical AI 応用1 最終課題');page=0;y=0
def p(text,size=9.5,bold=False,gap=8,color=NAVY,x=None,width=None):
    global y
    x=L if x is None else x;width=CW if width is None else width
    obj=Paragraph(text,ParagraphStyle('p',fontName='JB' if bold else 'JP',fontSize=size,leading=size*1.6,textColor=color,wordWrap='CJK'))
    _,h=obj.wrap(width,1000);assert y-h>=46,(page,text[:40],y,h)
    obj.drawOn(c,x,y-h);y-=h+gap
def label(text):p(text,11.5,True,7,TEAL)
def footer():
    c.setStrokeColor(LINE);c.line(L,34,W-L,34);c.setFont('JP',7.5);c.setFillColor(GRAY)
    c.drawString(L,22,'Physical AI 応用1 / 最終課題・v1.1 '+('検証レビュー（合格条件未達）' if review else '検証更新版'));c.drawRightString(W-L,22,f'{page} / 4')
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
def ps(v,g='runtime_english'):return next(s for s in probe['summary'] if s['model']==v and s['prompt_group']==g)
def count(s):return f"{s['k']} / {s['n']}"
def diagram():
    global y
    top=y;gap=20;bw=(CW-2*gap)/3
    for i,(head,lines) in enumerate([('入力',['画像・工程の指示','機体の状態']),('SmolVLA',['指定した人へ向かう','接近・停止の動作を生成']),('飛行と物理計算',['制御器・ArduPilotで安定化','MuJoCoで物理状態を更新'])]):
        x=L+i*(bw+gap);c.setFillColor(LIGHT);c.roundRect(x,top-77,bw,77,6,stroke=0,fill=1);c.setFillColor(TEAL);c.setFont('JB',10.5);c.drawString(x+10,top-22,head);c.setFont('JP',8.2);c.setFillColor(NAVY)
        for j,line in enumerate(lines):c.drawString(x+10,top-44-j*15,line)
        if i<2:
            c.setStrokeColor(TEAL);c.line(x+bw+3,top-39,x+bw+gap-3,top-39);c.line(x+bw+gap-3,top-39,x+bw+gap-7,top-36);c.line(x+bw+gap-3,top-39,x+bw+gap-7,top-42)
    # Preserve the submitted report's visible feedback loop.
    left=L+bw/2;right=L+2*(bw+gap)+bw/2;bottom=top-91
    c.setStrokeColor(TEAL);c.line(right,top-77,right,bottom);c.line(right,bottom,left,bottom);c.line(left,bottom,left,top-77)
    c.line(left,top-77,left-3,top-81);c.line(left,top-77,left+3,top-81)
    y=top-101;p('Blenderが次のカメラ画像を描画し、VLAへの入力に戻す',8.2,color=GRAY,gap=12)

start('PHYSICAL AI','災害救助ドローン','言葉による指示で捜索を任せ、操縦の負担を減らす',True)
if review:p('固定検証のレビュー版：事前に定めた完了の合格条件は未達。',9,True,color=colors.HexColor('#9B403B'))
label('01  目的と仕組み')
p('人が立ち入りにくい建物を、小型ドローンで捜索する。機体ごとに人が操縦する負担を減らすため、言葉で任務を伝え、対象者を探して確認画像を残す仕組みを制作した。被災した建物を想定した1室で、一連の動作を実装・検証した。')
p('離陸 → 見回し → 発見確認 → 接近・停止 → 確認画像の保存 → 着陸',9.3,True,12)
diagram()
label('VLAが人を認識し、近づき、止まる')
p('画像から指定された色の人を選び、その人へ接近し、止まる動作をVLAが生成する。対象の座標や検出枠は渡さない。「認識」は対象に応じた動作で検証し、VLAが別途人物検出ラベルを出す構成ではない。',9.1)
table(['担当','役割'],[
    ('任務管理','工程の順序・完了判定、再旋回・再捕捉・時間切れを管理'),
    ('SSDlite＋色判定','人物と服の色を判定し、連続3画像で「発見」を確認'),
    ('SmolVLA','画像・工程の指示・機体状態から、速度・旋回・離着陸要求の6成分を生成'),
    ('制御器・ArduPilot','離陸・定角旋回・着陸を実行し、飛行を安定化。人物を選ぶ接近・減速・停止はVLAが担当')],[108,CW-108])
p('VLAには過去の画像列や任務履歴を入力しない。画像に現れない工程の進み具合は任務管理が持ち、発見は独立した検出器で確認する。検出器は接近先への速度を生成しない。この分担は誤りを必ず防ぐという保証ではない。',8.8)
p('上位の「青い服の人を探して」はVLAへ直接渡さない。v1.1では、任務管理が「Approach the person wearing blue and stop.」などの英語の工程指示へ切り替える。任意の文章から捜索手順を計画する機能ではない。',8.6,color=GRAY,gap=0)

start('IMPLEMENTATION','飛行制御への追加学習','位置と色の結び付きを崩し、指定した相手を選ぶ動作を学習')
label('02  ドローンに合わせた動作と教師データ')
p('事前学習済みのSmolVLAを用い、画像や指示、機体の状態と飛行動作を対応付けた。動画のv1.0に加え、配置変更で見つかった弱点を直すため、別のモデルv1.1を追加学習した。')
table(['項目','内容'],[
    ('入力と動作','320×240 RGB画像、工程指示、9成分の機体状態。6成分の動作を32ステップ分生成'),
    ('v1.0','外観適応5,000ステップ＋停止改善4,000ステップ。最終段階は2,408画像・19,224教師例'),
    ('v1.1のデータ','20配置・6,000枚を生成。服色交換3,000組には、後方や画面端からの視点も含む。既存2,408枚も保持'),
    ('学習の組み方','服色・指示の交換と、同じ画像で水平速度を変える組を学習。停止の教師は推定速度と姿勢を利用。旋回の遅れも考慮した。損失の重みは水平各8、旋回4、他は各1'),
    ('更新する部分',f"色を学ぶ段階では動作生成部と一部のテキスト層を更新。最後の減速・旋回の学習では画像・言語の重みを固定。計{sum(h['steps'] for h in history):,}ステップ（{len(history)}段階）。各段階の最終重みを使用")],[91,CW-91])
p('開発では対象選択とは別に、静止や旋回で失敗が残った。VLAは人物を選んで接近・停止する動作を担い、決められた離陸・定角旋回・着陸は通常の制御に分離した。接近中の前後・左右・上下・旋回はVLA由来の指令を採用し、上限を適用して20Hzの速度制御とArduPilotで安定化する。',8.7,gap=8)
p('通常の制御は機体自身の推定状態を使い、人物の位置・画像・検出枠を使わない。接近終了はVLAの停止指令・推定速度・発見確認から判定する。水平速度の上限は0.2m/s、VLAの旋回速度は0.35rad/s。各変更の寄与を分離した比較ではない。',8.6,gap=8)
label('停止精度を改善した経緯')
p('外観適応前後の停止時間（青／赤）は0.00／0.00秒→2.97／3.07秒。教師が補正を止める範囲を25cmから4cmへ狭めた停止改善では、2.63／3.87秒→5.75／4.67秒となった。',9.2,gap=5)
p('前者では描画版、後者では工程判定も変更しており、追加学習だけの効果ではない。今回の比較は両モデルに同じ新版の制御器を使用する。旧制御器との違いを学習の効果に含めない。各数値の元記録はREADMEから参照できる。',8.4,color=GRAY)
label('実行中に正解の座標を渡さない')
p('人物の正解座標や距離は、実行中のVLA・人物判定・任務管理へ渡さない。検出枠もVLAの入力に含めない。真値は教師データ作成、描画・センサー合成、飛行後の採点に限って利用する。入力画像・動作列・機体状態・工程を保存し、失敗も全件追えるようにした。',9.2)
p('停止は人物の前0.9mの目標点から25cm以内・水平速度0.08m/s以下を3秒以上。画像保存・着陸中の静止は含めない。物理基準は維持し、離着陸の要求元だけを新しい分担に合わせた。旧判定結果も保存している。',8.4,color=GRAY,gap=0)

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
label('v1.1での再現結果')
assert len(report['regression_cases'])==9
reg_success=sum(r['success'] for r in report['regression_cases']);reg_fail=[r['case']['id'] for r in report['regression_cases'] if not r['success']]
p(f'英語の指示で、青・赤への接近、右→左と左だけの旋回、通常視界の青・赤の捜索、薄い霧・濃い霧・粉じんでの捜索を確認し、計9件中{reg_success}件に成功した。動画は英日併記の指示と旧制御器によるv1.0の記録で、新版の映像へ置き換えていない。',9.2)
if reg_fail:p('不合格の試験：'+'、'.join(LABELS.get(n,n) for n in reg_fail)+'。成功・失敗の全件をREADMEと記録に掲載する。',8.4,color=colors.HexColor('#9B403B'))
p('今回の学習用描画濃度0.004に対し、霧・粉じんの評価値は0.06／0.12。描画パラメーターとして15～30倍であり、実際の視程や粒子濃度の倍率ではない。発見は検出器が担い、VLAはその視界下での接近・停止などを生成する。',8.8)
label('実機での飛行は未検証')
p('実在するStampFlyとカメラ、制御用PCを組み合わせ、映像と飛行指令を無線で送受信する構成を検討した。今回は総質量50gの設計条件でのシミュレーションであり、搭載・電源・通信・実機飛行の成立を実測確認したものではない。',9.2,gap=0)

start('VALIDATION / v1.1','配置を変えて、対象の選択を検証','配置への依存を調べ、学習と実行方法を見直して固定再確認')
label('04  位置への依存を調べる')
known_text='今回のモデルはこの既知の失敗配置で成功した（1回）。' if report['known_failure_retest_passed'] else '今回のモデルも、この既知の失敗配置での再確認は不合格だった（1回）。'
p('配置交換で青を探させると、v1.0は対象を見失った。採点用目標点への最短距離は青が1.218m、元の青の位置にいる赤が0.204mだった。位置への依存が疑われ、位置と服色の組み合わせを変えて学習し直した。'+known_text,9.2)
p('前回の固定確認は新版11/16、動画回帰8/9。接近指令を飛ばして減速部分を使う実行方法を見直し、動作列を受信後に先頭から実行する方式に固定した。以下は同じ4配置×2色×2開始条件の再確認（位置±5cm、向き±5度）。配置は学習には未使用だが、実行方式の検討に使っており、独立した新規評価ではない。両モデルに同じ制御器・英語を使い、重み・ゲイン・採点を変えず、失敗も全件含めた。',8.5)
table(['最終評価','v1.0','v1.1'],[(label,count(stat('v1.0',g,k)),count(stat('v1.1',g,k))) for g,k,label in [('all',None,'全試験'),('color','blue','青い服への指示'),('color','red','赤い服への指示')]],[CW-180,90,90],size=9)
if review:p('事前基準：全体14/16以上・各色7/8以上・各配置3/4以上。動画9/9・既知失敗配置1/1、静止画像60/64・4通り正解14/16組も必須。基準を変更せず、不合格として記録した。',8.2,True,color=colors.HexColor('#9B403B'),gap=7)
failed_heldout=[r for r in read(BASE/'reports/receipt_failure_details.json')['failures'] if r['case']['model']=='v1.1' and r['case']['group']=='matched_unseen']
if failed_heldout and all(r['reasons']==['target_region_low_speed_hold_under_3s'] and r['target']['minimum_goal_distance_m']<=.25 for r in failed_heldout):
    holds=[r['target']['hold_s'] for r in failed_heldout]
    p(f"新版の不合格{len(holds)}件はいずれも指定色の目標範囲に入ったが、停止は{min(holds):.2f}～{max(holds):.2f}秒。接近後の停止の持続が未解決である。",8.5,gap=5)
s=stat('v1.1');p(f"参考：独立性を仮定したv1.1の95% Wilson区間は{s['wilson95'][0]*100:.1f}～{s['wilson95'][1]*100:.1f}%。同じ部屋の関連した少数試験であり、任意の環境での信頼性を表さない。",8.3,color=GRAY,gap=9)
image(BASE/'figures_navfocus/probe_01.png')
a,b=ps('v1.0'),ps('v1.1')
p(f"32画像で青・赤の英語指示を交換。もう一方の目標より指示した目標の方向に近い出力はv1.0 {a['correct_goal']}/{a['outputs']}、v1.1 {b['correct_goal']}/{b['outputs']}。角度差の中央値は{a['median_goal_angle_deg']:.1f}度→{b['median_goal_angle_deg']:.1f}度。服色交換×指示交換の4通りすべて正解はv1.1 {b['whole_quartet_correct']}/{b['quartets']}組。",8.7,gap=7)
p('図は事前指定した例。中央・右は水平面で、矢印はVLAの先頭10ステップの平均速度の向き（長さは統一）。静止・同点は不正解。制御器を通す前の動作を調べる検査であり、飛行成功率とは区別する。',8.1,color=GRAY,gap=8)
p('確認範囲は同じ部屋・同じ2人の外見・静止人物・限定した配置と英語の工程指示。未知の部屋、移動人物、複数室は未検証。学習・英語への適応・制御変更の寄与を個別に分離した実験ではない。',8.5,gap=8)
p('<link href="https://github.com/curio184/pai2026" color="#087F7F">github.com/curio184/pai2026</link>：READMEに事前条件・全実行・学習記録・モデルSHAを掲載。出典：SmolVLA / LeRobot、ArduPilot、MuJoCo、Blender、SSDlite、StampFly ecosystem、MakeHuman、Poly Haven（docs/THIRD_PARTY.md）。',8,color=GRAY,gap=0)
footer();c.save();reader=PdfReader(str(OUT));assert len(reader.pages)==4
full='\n'.join(p.extract_text() for p in reader.pages);(BASE/('reports/report_receipt_review_extracted.txt' if review else 'reports/report_receipt_extracted.txt')).write_text(full,encoding='utf-8')
assert all(t in full for t in ['v1.0','v1.1','未検証','連続3画像','0.08','16'])
(BASE/('reports/pdf_receipt_review_check.json' if review else 'reports/pdf_receipt_check.json')).write_text(json.dumps(dict(pages=4,pdf_sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(),original_pdf_modified=False,visually_reviewed=False,goal_met=report['preregistered_goal_met'],selected_checkpoint_sha256=selected['checkpoint_sha256']),indent=2))
print(OUT)
