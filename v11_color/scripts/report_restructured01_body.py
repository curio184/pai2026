"""Pages 2–4: implementation, demonstration, and evidence, in reader order."""

start('IMPLEMENTATION','学習から飛行制御まで','お手本を作る → 追加学習する → 飛行につなぐ')
label('02  実現方法')
p('SmolVLAを飛行制御に対応させるため、追加学習を行った。動画のv1.0を基に、人物配置への対応と実行方法を改善した更新版をv1.1とする。',9.3)

label('お手本の動作を作る')
p('シミュレーター内の人物位置と機体状態から、指定された人物に近づき、減速して止まる動作を計算する。その場面の画像・指示・機体状態と組にして、教師データを作った。',9.3)
table(['学習に使う情報','内容'],[
 ('入力','カメラ画像、英語の工程指示、機体の速度・高度・姿勢などの状態'),
 ('お手本','前後・左右・上下の速度、旋回速度、離陸・着陸の要求。0.1秒刻みで32ステップ分の動作列')
],[108,CW-108],size=9)
p('人物位置は教師データの作成に使い、VLAの入力には含めない。画像は物理シミュレーションの機体状態に合わせて描画する。',8.5,color=GRAY)

label('位置に頼らず、指示した色を選ぶよう学習する')
p('同じ部屋で人物を20通りに配置し、同じ位置・視点のまま服の色を交換した3,000組、6,000画像を用意した。同じ画像でも指示する色を変え、近づく相手が変わる組を学習させた。既存の2,408画像も残した。',9.3)
p('画像の特徴を取り出す部分は固定し、動作を生成する部分と言語処理の一部を追加学習した。後段では言語側も固定した。試験には、最後の学習ステップで保存した重みを使った。',9.1)

label('推論中の機体の移動に対応する')
p('画像を撮ってから動作を実行するまでにも、機体は動く。秒速20cmなら1秒で20cm進むため、撮影時の位置を前提とした指令では止まりにくい。',9.3)
p('実行部は、教師データで定義した速度と移動量の関係を使い、VLAの動作列から到達先を読み取る。撮影後に機体が動いた分を、機体自身の推定状態を使って補正し、その計画に追従する。',9.2)
p('撮影と推論を並行させ、待ち画像は最新の1枚に限定した。出力差を事前の基準で確認したうえで、推論の反復回数を10回から5回に減らした。動作列の長さは32のままとした。',9.1)
p('同じ開発条件で、画像更新間隔の中央値は1.33秒から0.46秒、指令採用時の画像の経過時間は平均1.88秒から1.16秒となった。処理構成全体を変えた比較であり、各変更の効果を個別に示すものではない。',8.5,color=GRAY)
p('学習設定・教師の計算式・重みの識別情報・処理時間の全記録は、READMEに掲載。',8.3,color=GRAY,gap=0)


start('DEMONSTRATION','捜索から着陸まで','青・赤の人物と、霧・粉じんのある場面で動作を確認')
label('03  実演結果')
p('動画のv1.0では、対象者の発見・接近・停止、確認画像の保存、着陸まで完了した。更新版v1.1でも同じ9場面で成功した。',9.5)

image_row([(name,ROOT/f'rescue_search/runs/eval03/{condition}_blue/notification.jpg') for name,condition in [('通常','clear'),('薄い霧','fog_light'),('濃い霧','fog_dense'),('粉じん','dust')]],height=72)
p('各条件で保存した確認画像（v1.0）。VLAに入力した機体カメラの画像を使用。',8.5,color=GRAY,gap=12)

label('発見・接近・画像保存・着陸を確認')
reg_by_id={row['case']['id']:row for row in report['regression_cases']}
rows=[]
for target,condition,key,color,rid in [
 ('青い服','通常','eval03/clear_blue','blue','search_clear_blue'),
 ('青い服','薄い霧','eval03/fog_light_blue','blue','search_fog_light_blue'),
 ('青い服','濃い霧','eval03/fog_dense_blue','blue','search_fog_dense_blue'),
 ('青い服','粉じん','eval03/dust_blue','blue','search_dust_blue'),
 ('赤い服','通常','eval_red01/clear_red','red','search_clear_red')]:
    old=read(ROOT/'rescue_search/runs'/key/'search_score.json')
    new=reg_by_id[rid]
    assert old['success'] and new['success']
    hold=old['physical']['goal_holds'][color]['physical_hold']['duration_s']
    rows.append((target,condition,f'{hold:.2f}秒',f"{new['hold_s']:.2f}秒"))
table(['対象','視界条件','v1.0の停止時間','v1.1の停止時間'],rows,[85,106,160,CW-351],size=9)
p('全条件で任務を完了。各モデル・各条件1回の確認。停止の判定基準と反復試験は次ページに示す。',8.6,color=GRAY)

assert len(reg_by_id)==9 and all(row['success'] for row in reg_by_id.values())
p('v1.1の再現確認は9/9成功。捜索5条件に加え、青・赤への接近、右→左と左のみの旋回を各1回確認した。',9.2,True)
p('動画のv1.0は英日併記の指示と旧実行方式、今回のv1.1は英語の指示と更新した実行方式を使用した。',8.5,color=GRAY)

label('追加学習に使っていない視界条件')
p('今回の追加学習画像の描画濃度は0.004。薄い霧は0.06、濃い霧・粉じんは0.12で評価した。これは描画パラメーターの違いであり、実際の視程や粒子濃度の倍率ではない。発見の確認は検出器、接近・停止の動作生成はVLAが担う。',9)

label('実機への展開')
p('実在するStampFlyにカメラを組み合わせ、制御用PCと映像・指令を無線で送受信する構成を検討した。今回は総質量50gの設計条件でのシミュレーションであり、搭載・電源・通信を含む実機での動作は未検証である。',9,gap=0)


start('VALIDATION','色で選べることを検証','配置の暗記ではないか、言葉を使っているか、繰り返し成功するか')
label('04  検証')

label('学習に使っていない人物配置で飛ばす')
assert report['known_failure_retest_passed']
p('v1.0は、青と赤の位置を交換すると、指定した青ではなく元の青の位置にいる赤へ向かった。服色と配置を変えて追加学習し、新しい4配置で旧版と新版を比較した。既知の失敗配置も、v1.1では成功した。',9.1)
p('4配置×2色×2開始状態の16条件を事前に固定した。開始位置は±5cm、向きは±5度の範囲で変え、同じ条件で両モデルを飛ばした。試験中の重み・制御係数・成功基準の変更や、失敗後の再試行は行っていない。',8.8)
def refstat(g='all',key=None):
    return next(s for s in report['reference_statistics'] if s['group']==g and s['key']==key)
assert report['reference_independently_rescored']
table(['条件','v1.0：共通変換','v1.0：対応変換','v1.1'],[
    (name,count(stat('v1.0',g,k)),count(refstat(g,k)),count(stat('v1.1',g,k)))
    for g,k,name in [('all',None,'全16条件'),('color','blue','青い服'),('color','red','赤い服')]
],[CW-267,94,94,79],size=8.8)
p('旧版は新版と同じ変換に加え、旧版の教師の動作定義に合わせた変換でも比較した。追従制御は共通。学習言語や教師の定義も異なるため、成績差を追加学習だけの効果とはしない。',8.2,color=GRAY,gap=8)

heldout_holds=[row['hold_s'] for row in report['final_cases'] if row['case']['model']=='v1.1' and row['case']['group']=='matched_unseen']
assert len(heldout_holds)==16
p(f"停止は、人物の前0.9mの目標点から25cm以内・水平速度0.08m/s以下を3秒以上とし、飛行後の真値で採点した。新版は4配置とも4/4成功し、停止は{min(heldout_holds):.2f}～{max(heldout_holds):.2f}秒継続した。画像保存・着陸中の静止は含めない。",8.8,gap=9)

label('指示と服の色を入れ替えて確かめる')
image(BASE/'figures_rebuild03/probe_01.png',width=480)
a,b=ps('v1.0'),ps('v1.1')
legacy=read(BASE/'probe_v10_language/outputs/summary.json')['summary'][0]
assert read(BASE/'reports/v10_language_reference_verified.json')['all_consistent']
p(f"16場面で服色を交換した32画像を用意し、各画像と機体状態を固定して青・赤の指示を入力した。指定側の目標点に近い向きは旧版{a['correct_goal']}/64、新版{b['correct_goal']}/64。旧版は元の英日併記でも{legacy['correct_goal']}/64。英語での角度差中央値は{a['median_goal_angle_deg']:.1f}度→{b['median_goal_angle_deg']:.1f}度だった。",8.8,gap=6)
p('矢印は制御前のVLA出力の先頭10ステップの平均水平速度。長さは統一し、静止・同点は不正解とした。図は事前指定した例。画像検査の正解数は、飛行の成功数と区別する。',8.1,color=GRAY,gap=9)

label('確認した範囲と記録')
p(f"検証範囲は同じ部屋・同じ2人の静止人物・限定した配置・英語の工程指示。未知の部屋と実機は未検証。失敗を含む{len(report['all_executed_cases'])}実行を保存し、異なる構成の成功数は合算しない。",8.7,gap=4)
p('設定・全記録・出典：<link href="https://github.com/curio184/pai2026" color="#087F7F">github.com/curio184/pai2026</link>（README／docs/THIRD_PARTY.md）',8.1,color=GRAY,gap=0)

footer()
c.save()
