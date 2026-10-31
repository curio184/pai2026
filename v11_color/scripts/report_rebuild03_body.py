# Executed by build_report_rebuild03.py with the established report helpers.
start('PHYSICAL AI','災害救助ドローン','言葉による指示で捜索を任せ、操縦の負担を減らす',True)
label('01  目的と仕組み')
p('人が立ち入りにくい建物を、小型ドローンで捜索する。機体ごとに人が操縦する負担を減らすため、言葉で任務を伝え、対象者を探して確認画像を残す仕組みを制作した。被災した建物を想定した1室で、一連の動作を検証した。')
p('離陸 → 見回し → 発見確認 → 接近・停止 → 確認画像の保存 → 着陸',9.3,True,12)
diagram()
label('VLAが人を認識し、近づき、止まる')
p('VLAが画像と言葉から指定色の人を選び、接近・減速・停止の動作列を生成する。実行部はその動作列から到達先を読み取り、機体自身の動きを補正しながら追従する。人物の正解座標や検出枠は、どちらにも渡さない。',9.2)
table(['担当','役割'],[
 ('任務管理','工程の順序・完了判定、再旋回・再捕捉・時間切れを管理'),
 ('SSDlite＋色判定','人物と服の色を判定し、連続3画像で「発見」を確認'),
 ('SmolVLA','画像・英語の工程指示・機体状態から、速度・旋回・離着陸要求の6成分を32ステップ分生成'),
 ('実行部・ArduPilot','VLAの動作列が示す到達先へ追従し、飛行を安定化。離陸・定角旋回・着陸は通常の制御で実行')],[108,CW-108],size=8.7)
p('VLAには過去の画像列や任務履歴を入力しない。画像に現れない工程の進み具合は任務管理が保持し、発見は独立した検出器で確認する。検出器は接近先への速度を生成せず、対象を見失った場合は任務管理が再捕捉や着陸へ切り替える。',8.8)
p('上位の「青い服の人を探して」はVLAへ直接渡さず、「Approach the person wearing blue and stop.」などの英語の工程指示に切り替える。「認識」は対象に応じた動作で検証しており、VLAが別途人物検出ラベルを出力する構成ではない。',8.5,color=GRAY,gap=0)

start('IMPLEMENTATION','学習と飛行制御','VLAが相手を選び、機体の動きに合わせて計画を実行する')
label('02  色と配置を切り離して学習')
p('事前学習済みSmolVLAを、画像・指示・機体状態と飛行動作の組で追加学習した。動画のv1.0とは別に、人物配置を変えたときの弱点を修正するモデルv1.1を用意した。',9.2)
table(['項目','内容'],[
 ('入力・出力','320×240 RGB画像、工程指示、9成分の推定機体状態。6成分×32ステップ（0.1秒刻み）の動作列'),
 ('v1.1のデータ','20配置・6,000画像。服色を交換した3,000組と、既存の2,408画像を保持。同じ画像で指示や速度状態を変える組も学習'),
 ('学習と重み',f"動作生成部と一部のテキスト層を更新し、後段では画像・言語の重みを固定。累計{sum(h['steps'] for h in history):,}ステップ・{len(history)}段階。最終段階は6,000ステップの最終重みを使用")],[90,CW-90],size=8.6)
label('画像が古くなる間にも、機体は動く')
p('画像の取得から指令の実行までに遅れがあると、生成時に想定した位置を通り過ぎる。速度0.2m/sなら1秒で20cm進み、停止範囲25cmに対して無視できない。動作列の実行起点を変えるだけでは、停止の問題を解決できなかった。',9.1)
p('そこで、VLAの速度列と撮影時の機体状態から、教師の動作定義に従って到達先を復元した。撮影後に移動した量を機体自身の推定速度から補正し、20Hzの制御で追従する。到達先と停止の意図はVLA出力に依存し、人物座標から誘導する制御には置き換えていない。',9.1)
p('撮影と推論を並行させ、待ち画像は最新の1枚だけにした。推論の反復回数は、事前に定めた出力差の基準を満たす5回へ削減。動作列の長さ32は維持した。古い画像を許容する上限や、停止の採点基準は緩めていない。',8.8)
latency=read(BASE/'reports/rebuild_latency_same_case.json')
# The detailed measurements remain in the linked record; this concise example
# compares the complete configurations, not an isolated causal treatment.
p('同じ開発条件では、画像更新間隔の中央値が1.33秒から0.46秒、VLAの指令採用時の画像経過時間の平均が1.88秒から1.16秒となり、捜索から着陸まで成功した。処理構成の寄与を個別に分離した比較ではない。',8.6,color=GRAY)
label('停止の基準と、正解情報の分離')
p('停止は人物の前0.9mの目標点から25cm以内・水平速度0.08m/s以下を3秒以上。画像保存・着陸中の静止は除く。成功した接近は、新しいVLAの計画を採用した状態だけでも3秒以上停止したことを、保存記録から照合した。',8.8)
p('真値の使用は教師作成・描画・機体センサーの合成・飛行後の採点に限定する。実行時は機体自身の推定状態で動きを補正する。生のVLA出力と変換後の指令を別々に保存し、速度列をそのまま実行したとは記載しない。',8.5,color=GRAY,gap=0)

start('RESULTS / VIDEO v1.0','発見から着陸までを確認','動画はv1.0で撮影。v1.1でも同じ9場面の成功を確認')
label('03  動画で示した結果と実機への展開')
image_row([(name,ROOT/f'rescue_search/runs/eval03/{condition}_blue/notification.jpg') for name,condition in [('通常','clear'),('薄い霧','fog_light'),('濃い霧','fog_dense'),('粉じん','dust')]])
p('実際のモデル入力に由来する確認画像。外部視点の動画は記録した位置・姿勢から再描画し、VLA入力欄には保存した原JPEGを表示した。',8.3,color=GRAY,gap=10)
rows=[]
for target,condition,key,color in [('青い服','通常','eval03/clear_blue','blue'),('青い服','薄い霧','eval03/fog_light_blue','blue'),('青い服','濃い霧','eval03/fog_dense_blue','blue'),('青い服','粉じん','eval03/dust_blue','blue'),('赤い服','通常','eval_red01/clear_red','red')]:
 s=read(ROOT/'rescue_search/runs'/key/'search_score.json');assert s['success'];rows.append((target,condition,'完了',f"{s['physical']['goal_holds'][color]['physical_hold']['duration_s']:.2f}秒"))
table(['対象','視界条件','v1.0の捜索','停止の継続時間'],rows,[80,100,160,CW-340])
p('v1.0の表は1室・固定配置で各条件1回の最終確認。完了は発見、接近・停止、画像保存、着陸・モーター停止を含む。一般的な成功率を示す統計ではない。',8.7)
label('v1.1でも動画の9場面を再現')
assert len(report['regression_cases'])==9 and all(r['success'] for r in report['regression_cases'])
p('各場面1回の再現確認で、青・赤への接近、右→左と左だけの旋回、通常視界の青・赤の捜索、薄い霧・濃い霧・粉じんでの捜索は9件すべて成功した。動画は英日併記の指示と旧制御器によるv1.0の記録。今回は英語の指示と新版の実行部を使った。',9.1)
p('今回の追加学習画像の描画濃度0.004に対し、霧・粉じんの評価値は0.06／0.12。描画パラメーターとして15～30倍であり、実際の視程や粒子濃度の倍率ではない。人物の発見は検出器、視界不良の画像から接近・停止の動作を生成する役割はVLAが担う。',8.8)
p('既存記録の停止時間（青／赤）：外観適応前後は0.00／0.00秒→2.97／3.07秒、教師の補正停止範囲25cm→4cmの前後は2.63／3.87秒→5.75／4.67秒。描画版や工程判定も変わっており、学習だけの効果ではない。採点原票はREADMEから参照できる。',8.3,color=GRAY)
label('実機での飛行は未検証')
p('実在するStampFly、カメラ、制御用PCを組み合わせ、映像と指令を無線で送受信する構成を検討した。今回は総質量50gの設計条件でのシミュレーションであり、搭載・電源・通信・実機飛行の成立を実測確認したものではない。',8.8,gap=0)

start('VALIDATION / v1.1','配置を変えて、色で選べるか','弱点の分析 → 学習と実行方法の修正 → 未学習配置で固定検証')
label('04  位置への依存を調べる')
assert report['known_failure_retest_passed']
p('配置交換で青を探させると、v1.0は元の青の位置にある赤へ向かい、対象を見失った。採点用目標点への最短距離は青1.218m、赤0.204m。位置への依存を疑い、服色と配置の組を変えて学習した。v1.1はこの既知の失敗配置でも成功した。',9)
p('新しい4配置×2色×2開始条件（位置±5cm、向き±5度）を事前に固定。英語・追従制御・物理基準は共通とした。教師の速度定義が異なるため、旧版は共通変換の16件に加え、旧版の教師定義に対応した変換でも16件を確認し、両方を残した。',8.6)
def refstat(g='all',key=None):return next(s for s in report['reference_statistics'] if s['group']==g and s['key']==key)
assert report['reference_independently_rescored'] and report['publication_evidence_complete']
table(['固定試験','旧版：共通','旧版：対応','新版'],[(name,count(stat('v1.0',g,k)),count(refstat(g,k)),count(stat('v1.1',g,k))) for g,k,name in [('all',None,'全試験'),('color','blue','青い服への指示'),('color','red','赤い服への指示')]],[CW-240,80,80,80],size=8.8)
layout_counts=[s for s in report['heldout_statistics'] if s['model']=='v1.1' and s['group']=='layout']
heldout_holds=[r['hold_s'] for r in report['final_cases'] if r['case']['model']=='v1.1' and r['case']['group']=='matched_unseen']
p('v1.1の配置別成功数：'+'、'.join(f"配置{i+1} {s['k']}/{s['n']}" for i,s in enumerate(layout_counts))+f"。停止の継続は{min(heldout_holds):.2f}～{max(heldout_holds):.2f}秒。事前基準は全体14/16以上・各色7/8以上・各配置3/4以上。動画9/9と既知配置1/1、下記の画像検査も満たした。",8.3,gap=8)
image(BASE/'figures_rebuild03/probe_01.png')
a,b=ps('v1.0'),ps('v1.1')
legacy_language=read(BASE/'probe_v10_language/outputs/summary.json')['summary'][0]
assert read(BASE/'reports/v10_language_reference_verified.json')['all_consistent']
p(f"32画像で指示と服色を交換。指示した目標の方向に近い出力はv1.0 {a['correct_goal']}/{a['outputs']}、v1.1 {b['correct_goal']}/{b['outputs']}。旧版は本来の英日併記でも{legacy_language['correct_goal']}/64だった。英語での角度差中央値は{a['median_goal_angle_deg']:.1f}度→{b['median_goal_angle_deg']:.1f}度。4通りすべて正解はv1.1 {b['whole_quartet_correct']}/{b['quartets']}組。",8.7,gap=7)
p('矢印は制御前のVLAの先頭10ステップの平均水平速度の向き（長さは統一）。静止・同点は不正解。図は事前指定した例で、全出力を保存した。静止画像の検査は飛行成功率とは区別する。',8.1,color=GRAY,gap=8)
p(f"v1.1開発以降の追加検証は、失敗を含む{len(report['all_executed_cases'])}実行を記録し、異なる構成の成功数を合算しない。確認範囲は同じ部屋・同じ2人・静止人物・限定した配置と英語の工程指示。未知の部屋や実機は未検証。v1.0の学習言語は英日併記のため、言語適応の効果も分離していない。",8.4,gap=8)
p('<link href="https://github.com/curio184/pai2026" color="#087F7F">github.com/curio184/pai2026</link>：READMEに役割分担、事前条件、全実行、モデルSHAと根拠を掲載。出典：SmolVLA / LeRobot、ArduPilot、MuJoCo、Blender、SSDlite、StampFly ecosystem、MakeHuman、Poly Haven（docs/THIRD_PARTY.md）。',8,color=GRAY,gap=0)
footer();c.save();reader=PdfReader(str(OUT));assert len(reader.pages)==4
full='\n'.join(p.extract_text() for p in reader.pages);(BASE/'reports/report_rebuild03_extracted.txt').write_text(full,encoding='utf-8')
assert all(t in full for t in ['v1.0','v1.1','未検証','連続3画像','0.08','16','到達先'])
(BASE/'reports/pdf_rebuild03_check.json').write_text(json.dumps(dict(pages=4,pdf_sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(),original_pdf_modified=False,visually_reviewed=False,goal_met=report['preregistered_goal_met'],selected_checkpoint_sha256=selected['checkpoint_sha256']),indent=2))
print(OUT)
