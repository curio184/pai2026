"""Review README for the English final candidate; no Git mutation or publication."""
import hashlib,json
from pathlib import Path
from training_history import lineage
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=read(W/'results/all_trials_round02_english.json');assert r['preregistered_goal_met']
selected=read(W/'protocol/selected_final_round02_english.json');candidate=selected['candidate']
probe=read(W/'probe_round02_english/outputs/summary.json')
exposure=read(W/'models'/candidate/'sampling_exposure.json');history=lineage(W,candidate)
assert candidate=='train16_en', 'Update the description to match any later training recipe'
source_candidate=candidate
data_manifest=read(W/'data/dataset16_en/manifest.json')
visibility=read(W/'reports/v11_training_visibility_train16.json')
assert visibility['verified'] and visibility['dataset_audit_sha256']==sha(W/'data/dataset16_en/audit.json')
final_completion=read(W/'reports/train16_final_checkpoint_completion_audit.json')
assert final_completion['passed'] and final_completion['final_sha256']==selected['checkpoint_sha256']
source=Path('<WORK_ROOT>/repository/README.md');text=source.read_text(encoding='utf-8')
def stat(version,group='all',key=None):return next(s for s in r['heldout_statistics'] if s['model']==version and s['group']==group and s['key']==key)
def count(s):return f"{s['k']}/{s['n']}（{s['k']/s['n']*100:.1f}%）"
def ps(version):return next(s for s in probe['summary'] if s['model']==version and s['prompt_group']=='runtime_english')
rows=[]
for group,key,label in [('all',None,'全試験'),('color','blue','青い服への指示'),('color','red','赤い服への指示')]:rows.append(f"| {label} | {count(stat('v1.0',group,key))} | {count(stat('v1.1',group,key))} |")
for layout in read(W/'protocol/round02_english.json')['heldout_layouts']:
    key=layout['name'];rows.append(f"| 配置 {key[-2:]} | {count(stat('v1.0','layout',key))} | {count(stat('v1.1','layout',key))} |")
training_rows=[]
for h in history:
    plan=next(p for p in (W/'protocol').glob('*.json') if sha(p)==h['plan_sha256'])
    training_rows.append(f"| {h['candidate']} | {h['steps']:,} | `{h['checkpoint_sha256'][:16]}…` | [事前条件](v11_color/protocol/{plan.name}) / [完了記録](v11_color/models/{h['candidate']}/result.json) |")
p0,p1=ps('v1.0'),ps('v1.1');s0,s1=stat('v1.0'),stat('v1.1')
final_suite='heldout_round02_english_'+candidate
assert len([x for x in r['all_executed_cases'] if x['suite']==final_suite])==32
section=f'''## v1.1：色と指示で相手を選べるかを検証する

**公開済み動画はv1.0の記録で、変更していません。** v1.1は提出後の追加検証と学習の成果です。提出時の版は[Release v1.0.0](https://github.com/curio184/pai2026/releases/tag/v1.0.0)に残しています。

### 弱点の発見と、失敗した評価を残す

青と赤の立ち位置を交換した試験で、v1.0は青を探す途中に対象を見失いました。採点用目標点への最短距離は青が1.218m、元の青の位置にいる赤が0.204mでした。人物そのものではなく、人物の前0.9mの目標点への距離です。位置への依存を示唆しますが、「位置しか見ていなかった」と断定はしません。[元の失敗記録](v11_color/prior/T3_failure_analysis.json)

そこで、位置・人物の外見・カメラ・機体状態を揃えたまま、服の色と指示を入れ替える教師データを作りました。最初の候補は開発試験4/8、次の候補は7/8。目標付近の学習例と速度の範囲を補い、停止後の余裕を確保するため教師の停止位置を10cm手前へ移しました。採点点と許容範囲は変更していません。[初回の全結果](v11_color/runs/dev_train01/summary.json) / [2番目の全結果](v11_color/runs/dev_train02/summary.json)

3番目の候補 `train03` は開発試験8/8と動画の動作9/9に成功しましたが、最初の最終評価では**旧モデル2/16、候補6/16**に留まりました。この評価は英日併記の指示で実施しています。候補は色・指示の入れ替え検査64/64には成功した一方、離陸後の静止不足、長い静止待ちによる時間切れ、旋回後の停止不足などが残りました。[32件の全結果](v11_color/runs/heldout_train03/summary.json) / [工程別の診断](v11_color/reports/heldout_train03_phase_diagnostic.json) / [当時の全推論](v11_color/probe/outputs/raw_outputs.jsonl)

この失敗を受け、静止・旋回・離陸中には、機体自身が推定した水平速度に応じて減速する動作を教師に追加しました。接近・着陸・鉛直速度・旋回速度・離着陸要求の教師は維持し、飛行制御器やそのゲイン、任務の完了判定も変えていません。これは教師の変更であり、実行時に別の制御則でVLA出力を置き換える処理ではありません。

併せて、利用する指示を**英語だけ**に統一しました。変更前の候補も、公開済みの評価画像で英語の指示を与える検査に64/64で成功しました。これは既知の画像を用いた開発用確認であり、最終評価の数値には加えません。[英語への変更記録](v11_color/protocol/english_language_amendment.json) / [英語への切り替え検査](v11_color/probe_english_transition/outputs/summary.json) / [指示文だけを変更した差分](v11_color/protocol/runtime_english.diff)

英語版の候補 `train04_en` は基本の開発試験8/8に成功した一方、既知の配置を用いた厳しい開発試験では10/16（青6/8・赤4/8）でした。全試験の成功条件を満たさなかったため、採用せず、新しい最終評価にも進みませんでした。既知の32画像での色・指示交換は64/64でしたが、これは飛行成功とは別の結果です。[16件の全結果](v11_color/runs/stress_train04_en/summary.json) / [失敗工程と入力画像](v11_color/reports/stress_train04_en_failure_details.json) / [色・指示交換の全出力](v11_color/probe_train04_english_dev_retry01/outputs/raw_outputs.jsonl)

そこで、後方へ流れた位置や、人物が画面の端にいる視点、さまざまな向きからの学習画像を追加しました。また、同じ画像・指示でも機体の水平速度が逆なら、減速の教師出力も逆になる組を用意しました。速度と動作の対応を学習しやすくするための設計であり、各変更の効果を個別に証明したものではありません。

この候補 `train05_en` も基本試験8/8に成功しましたが、厳しい開発試験は11/16でした。失敗5件は、捜索前の静止に時間がかかる、停止が3秒に届かない、人物の発見を確認できない、という経過でした。条件を緩めず、新しい最終評価は未着手のまま残しました。[16件の全結果](v11_color/runs/stress_train05_en/summary.json) / [全失敗と入力画像](v11_color/reports/stress_train05_en_failure_details.json)

次の学習では、離陸前の低高度で横移動を要求しない教師と、空中での減速、接近時に速度を落とす教師を用意しました。同じ画像・指示で水平速度を正負・ゼロ・半分に変える組も追加しました。実行時にVLA出力を別の制御で補正したものではなく、VLAが学ぶ動作を変更しています。

ただし、この候補 `train06_en` の結果は基本試験8/8、厳しい開発試験9/16で、改善には至りませんでした。離陸後の静止不足と、対象の前での停止不足が残りました。VLA出力の実行には画像取得から遅れがある一方、静止用の教師は取得時の速度に基づく補正をチャンク内で一定にしていました。この点を見直し、次の学習では静止・旋回・離陸時の水平速度の教師をゼロにしました。既存の低位制御器が現在の推定速度との差から姿勢を計算するためです。また、接近の教師の停止位置を採点点と同じ位置に戻し、目標付近で速度指令が小さくなりすぎないよう教師を見直しました。各変更の効果を分離した比較ではありません。[16件の全結果](v11_color/runs/stress_train06_en/summary.json) / [失敗と入力画像](v11_color/reports/stress_train06_en_failure_details.json) / [保存出力の診断](v11_color/results/train06_en_postflight_v2_development_diagnostic.json)

この候補 `train07_en` は基本試験7/8でした。8件とも離陸後の静止と各動作の停止条件を満たしましたが、1件で接近・停止後の着陸中に前へ流れ、人物との距離が0.447mとなりました。0.45mの基準を緩めず不合格とし、厳しい開発試験や最終評価には進めませんでした。次の候補では、それ以外の教師則を維持し、教師の停止位置だけを10cm手前に戻しました。これは学習上の安全余裕であり、採点の目標点は人物の前0.9mのままです。[8件の全結果](v11_color/runs/dev_train07_en/summary.json) / [距離不足の工程と時系列](v11_color/results/train07_dev02_clearance_development_diagnostic.json)

この候補 `train08_en` は基本試験8/8、厳しい開発試験8/16でした。離陸後の静止を3秒以上続けられたのは9/16、指定した対象の前での停止を3秒以上続けられたのは12/16です。これらは工程別の結果であり、捜索全体の成功率とは区別します。静止用に水平速度ゼロを学習させても横流れが残り、長い静止待ちや発見前の失敗がありました。[16件の全結果](v11_color/runs/stress_train08_en_capped/summary.json) / [工程別の採点](v11_color/reports/stress_train08_en_capped_phase_diagnostic.json) / [保存出力と教師の照合](v11_color/results/stress_train08_en_capped_postflight_development_diagnostic.json)

次の候補では、画像・指示・機体状態と接近の教師を維持し、離陸後・静止・旋回中の水平減速だけを見直しました。推定速度の0.6倍を逆向きに要求する教師を用い、低高度の離陸時には横移動を要求しません。上限や制御器を実行時に変更したものではなく、VLAが学習する動作の変更です。係数は新しい学習の前に固定しました。[学習前に記録した条件](v11_color/protocol/train09_english.json)

この候補 `train09_en` は基本試験7/8でした。青・赤への接近と左だけの旋回は成功しましたが、右→左の連続旋回で時間切れになりました。右旋回後に目標角を行き過ぎたまま小さな修正が続き、その工程に約61秒かかりました。次の学習では、空中での旋回について、教師が角度の補正を止める範囲を0.12radから0.03radへ狭め、学習損失の旋回成分の重みを1から4へ変更しました。画像・指示・状態と、それ以外の動作の教師は維持しています。成功の判定や制御器を変えたものではありません。[8件の全結果](v11_color/runs/dev_train09_en/summary.json) / [旋回中の角度と出力](v11_color/results/train09_rotation_development_diagnostic.json) / [次の学習条件](v11_color/protocol/train10_english.json)

この候補 `train10_en` は基本試験8/8、厳しい開発試験12/16でした。残る失敗は、長い静止待ちの後の着陸、離陸後の静止不足、旋回後の発見失敗、対象前の停止不足の4件です。画像を確認すると、発見に失敗した実行では旋回が行き過ぎ、対象が画面の左端へ外れていました。保存された出力と教師の照合でも、減速や旋回補正の差が残っていました。これは原因の候補を調べた診断であり、一つの原因に特定したものではありません。[16件の全結果](v11_color/runs/stress_train10_en/summary.json) / [出力と教師の照合](v11_color/results/stress_train10_en_postflight_development_diagnostic.json)

次の候補では教師と入力データを維持し、動作生成に使う乱数の学習条件を見直しました。本番は以前から一つの乱数系列に固定しているため、学習の半分に同じ系列を使い、残り半分ではランダムな系列を使いました。6,000ステップで終了すると事前に定め、途中の重みは評価していません。推論側の乱数、制御器、判定条件は変えていません。これを任意の生成乱数でも安定する証拠とは扱いません。[学習前に記録した条件](v11_color/protocol/train11_english.json)

この候補 `train11_en` も基本試験8/8、厳しい開発試験12/16でした。H06は長い静止待ちから時間切れ、H11は離陸後の実際の静止が1.4835秒で基準未達、H12は発見できず、H16は赤い人物を発見した後に画面の右端へ見失いました。成功した12件だけを選んでいません。[全16件](v11_color/runs/stress_train11_en/summary.json) / [失敗時の状態と画像の確認](v11_color/reports/train11_failure_analysis.json)

次の候補では、静止時の教師の減速係数を0.6から1.2へ変更しました。旋回の教師は、入力された旋回速度から1秒先の向きを予測して補正し、教師の旋回速度の上限を0.25rad/sとしました。開発試験で画像取得から最初の動作実行までの遅れが約0.91秒だったためです。これは学習用の動作の変更であり、実行時の制御器・ゲイン・上限は維持しています。接近・着陸の教師と入力画像・状態も維持しました。複数の変更と追加学習を含むため、各変更の効果を単独では主張しません。[学習前に記録した条件](v11_color/protocol/train12_english.json)

この候補 `train12_en` は基本試験7/8でした。青・赤への接近と旋回の単独試験は成功しましたが、青の捜索1件で、発見時から右端にいた対象者を接近中に見失いました。全8件を完走し、成功した7件だけを選んでいません。[全8件](v11_color/runs/dev_train12_en/summary.json) / [失敗の分析](v11_color/reports/train12_failure_analysis.json)

学習データを調べると、対象者が画面端にいる画像も含まれる一方、接近の教師では旋回をすべてゼロとしていました。次の候補では、同じ画像・指示・状態を使い、指定された人物へ向きを合わせながら接近する動作を教師に追加しました。移動の目標点と基本の速度計算は維持し、向きが変わることに合わせて動作列を計算しています。離着陸・静止・見回しの教師は変更していません。改善は仮説として事前に記録し、飛行で確認しました。追加学習と新しい乱数シードも含むため、旋回の教師だけの効果を切り分けた比較ではありません。[学習画像と教師の確認](v11_color/reports/navigation_training_geometry_audit.json) / [学習前に記録した条件](v11_color/protocol/train13_english.json)

この候補 `train13_en` は基本試験8/8、厳しい開発試験9/16でした。指定した人物への接近・停止は13/16、初期静止は14/16でしたが、これらを任務全体の成功率と置き換えていません。残る7件は初期静止2件、目標前での停止3件、着陸中の距離不足1件、確認工程の時間切れ1件です。長引いた1件では、電圧の低下とモーター出力の上限付近への到達、高度の低下も記録されています。これはシミュレーターの電源モデル上の挙動で、実機の飛行時間を測定した結果ではありません。[全16件](v11_color/runs/stress_train13_en/summary.json) / [全件報告](v11_color/reports/train13_completed_suite_report.txt) / [失敗の分析](v11_color/reports/train13_failure_analysis.json)

次の候補では、接近中にも入力された移動速度と旋回速度から1秒先の対象方向を予測する教師を用いました。また、静止時の教師の減速係数を1.2から1.6へ控えめに増やしました。画像・指示・機体状態、接近の目標点と水平速度の基本式、上下動・離着陸要求、見回しの旋回教師は維持しています。8,000ステップで終了すると事前に決め、実行時の制御器やゲイン、判定基準は変更していません。学習画像112例で計224出力を調べた事前の診断では、推論を1段階に減らす一貫した利点は得られず、本番の推論は10段階を維持しました。この診断は学習データ上の一致度であり、未知条件の性能評価ではありません。[次の学習条件](v11_color/protocol/train14_english.json) / [出力誤差の事前条件](v11_color/protocol/train13_fit_diagnostic.json) / [診断の全出力](v11_color/reports/train13_fit_diagnostic/raw_outputs.jsonl)

この候補 `train14_en` は基本試験6/8でした。青・赤への接近・停止6件と初期静止8件は成立しましたが、捜索1件と左旋回1件では、旋回終了前の横移動速度が0.119／0.116m/sとなり、上限0.08m/sを超えました。記録には前後の揺れが徐々に増える様子があり、遅れて届く状態に対する強い制動が一因と考えました。次の候補では、静止・旋回・離陸中の教師の減速係数だけを1.6から0.6へ下げ、6,000ステップを事前に定めました。入力と接近・着陸・旋回速度・上下動の教師は保持しています。この因果関係を単独で証明した比較ではありません。[全8件](v11_color/runs/dev_train14_en/summary.json) / [失敗の分析と波形](v11_color/reports/train14_failure_analysis.json) / [次の学習条件](v11_color/protocol/train15_english.json)

この修正後の候補 `train15_en` は基本試験8/8に成功しました。前の候補で失敗した2件の旋回終了前の最大水平速度は、0.119→0.025m/s、0.116→0.039m/sとなり、既存の0.08m/sの基準を満たしました。これは開発に使った既知の8件の比較であり、未学習配置での成功率とは別に扱います。[8件すべての比較](v11_color/reports/train15_development_comparison.json)

ただし、同候補の厳しい開発試験は9/16でした。対象前での停止は12/16、初期静止は13/16でしたが、工程単独の成立を任務全体の成功に置き換えていません。1件では姿勢推定のずれと横流れが続き、その後に電池低下・推力不足・クラッシュによる停止が記録されました。また、画像を保存しても目標点に届かない例や、着陸中に人物との距離が不足した例がありました。[全16件](v11_color/runs/stress_train15_en/summary.json) / [全件報告](v11_color/reports/train15_completed_suite_report.txt) / [保存記録の分析](v11_color/reports/train15_failure_analysis.json)

次の候補では、速度だけでなく、既に入力している姿勢の推定値も使う停止動作を教師にしました。実行時の制御器やVLAの入力は増やしていません。遅れと一定の外乱を置いた簡単な数式モデルで検討しましたが、その結果は飛行の成功率に含めません。画像・指示・機体状態と、接近・着陸・旋回速度・上下動の教師は保持しました。この変更だけの効果を切り分けた比較ではありません。[次の学習条件](v11_color/protocol/train16_english.json) / [数式モデルでの検討1](v11_color/reports/stationary_feedback_analysis01.json) / [検討2](v11_color/reports/stationary_feedback_analysis02.json)

### 学習データとモデル

同じ室内の20配置で、服色だけを交換した2,000組・4,000枚に加え、視点の範囲を広げた1,000組・2,000枚を生成しました。既存の2,408枚も保持し、画像は計8,408枚です。RGB画像、工程の指示、9成分の機体状態を入力し、水平・鉛直速度、旋回速度、離着陸要求の6成分を32ステップ分出力します。人物の正解座標・距離・検出枠はVLAへ入力しません。

色を学ぶ段階では画像エンコーダーを固定し、動作生成部とテキスト層の一部を更新しました。英語への統一後の減速・旋回の学習では画像・言語を処理する部分の重みを固定し、動作生成部と状態・動作の射影層を学習しました。最終ステップの重みだけを使い、途中の重みを成績で選んでいません。

最後の学習段階は、色・指示交換25%、接近の例25%、速度を変えた4例の組40%、離着陸・旋回・静止の既存例10%で構成しました。6成分を既存の尺度で正規化したうえで、水平2成分の学習損失を各8、旋回を4、残り3成分を各1の重みで平均しました。これは学習時の重み付けであり、実行時の出力単位や制御則は変えていません。教師例は{data_manifest['samples']:,}件、速度を変えた4例の組は{data_manifest['state_quartets']:,}組です。最後の段階でも同じ画像・指示・状態を再利用し、評価画像・状態を教師例に加えていません。[学習条件](v11_color/protocol/train16_english.json) / [データの照合記録](v11_color/data/dataset16_en/audit.json)

最終段階の静止・旋回・離陸後の教師は、推定水平速度を `v` として、`0.6*v - 0.9*9.81*tan([pitch, roll])` を水平速度の要求値とし、大きさを0.2m/s以下に制限します。角度はラジアン、出力は機体の前・左方向です。姿勢の項は直前の加速度要求の近似に使っており、真の姿勢誤差や過去の画像を入力するものではありません。取得時の値を32ステップで一定にし、未アーム時と高度25cm未満の離陸中は水平速度ゼロにします。[停止用教師の実装](v11_color/scripts/teacher_flight16.py)

接近の教師は人物の前1.0mを目標点とし、位置誤差に係数1.4を掛け、推定速度の0.5倍を差し引いて上限0.2m/sに制限した動作列を作りました。位置の補正を止める範囲は2cmです。空中での旋回の教師は、1秒先の予測方向と目標角との差に0.8を掛け、上限0.25rad/s、補正を止める範囲0.03radとしました。これらは学習用教師の値であり、実行時の旋回指令上限0.35rad/sや、採点の25cm・0.08m/s・3秒という基準は変更していません。上下移動・離着陸要求の既存教師も維持しています。人物の正解座標を使うのは教師作成と飛行後の採点などに限り、実行中には渡していません。

接近中の教師には、指定された人物がカメラの正面に来るように旋回する動作も加えました。入力の移動速度・旋回速度から1秒先の位置と向きを予測し、そのときの対象方向との差に0.8を掛けます。旋回速度は上限0.25rad/s、補正を止める範囲は0.05radです。向きの変化に合わせて、機体から見た水平速度も動作列の中で計算し直します。正解の人物位置を用いるのはオフラインの教師作成だけです。VLAが実行時に見るのは、従来どおり画像・工程指示・機体状態です。[教師の実装](v11_color/scripts/teacher_flight14.py) / [教師の方向と不変条件の確認](v11_color/reports/train16_teacher_preflight_audit.json)

保存された学習前後の重みをCPU上で読み直し、固定部分の一致と、変更が許可した学習対象に限られることも確認しました。[保存済み重みの照合](v11_color/reports/{source_candidate}_saved_training_verification.json)

最終段階は6,000ステップで終了し、その時点の学習対象パラメーター全155個が、保存した最終モデルと学習再開用ファイルで完全一致することを確認しました。最適化器のステップ数、学習ログ、教師例の使用回数も照合しています。[最終ステップの照合](v11_color/reports/train16_final_checkpoint_completion_audit.json)

| 学習段階 | 完了ステップ | 重みSHA-256の先頭 | 記録 |
| --- | ---: | --- | --- |
{chr(10).join(training_rows)}

最後の学習段階で使用した画像は新規{exposure['unique_new_images']:,}枚・既存{exposure['unique_retention_images']:,}枚、重複を含む教師例の使用回数は{exposure['total_samples']:,}回です。生成枚数と、実際に抽出した枚数を区別しています。[画像・動作・言語ごとの使用回数](v11_color/models/{candidate}/sampling_exposure.json)

採用モデルSHA-256：`{selected['checkpoint_sha256']}`

### 新しい配置での最終評価（英語の指示）

最初の最終評価は、その後の改善判断に利用したため、新モデルの未知条件の検証には使い直しません。**別の4配置と乱数シードを学習前に固定**し、旧モデルと採用モデルを同じ英語の指示・配置・開始条件で比較しました。配置は事前に決めた範囲から固定シードで4組生成し、成績による選別はしていません。[新しい事前条件](v11_color/protocol/round02_english.json)

v1.0の最終学習では英日併記の7種類の工程指示を用い、v1.1の後半の学習では英語だけを用いました。評価時の指示は両者で同じですが、学習時の言語条件への適応の影響は分離していません。結果の差を色・配置データだけの効果とは扱いません。[v1.0の学習指示](outputs/vla_data_realism_precision_02/manifest.json) / [英語への変更記録](v11_color/protocol/english_language_amendment.json)

実行時の推論記録についても、VLAに渡した指示文が英語であり、使用した重みが各試験の指定と一致することを全件確認しました。[実際の入力指示とモデルの照合](v11_color/reports/runtime_english_instructions_verified.json)

最終評価の4配置は、追加学習の20配置および保持した元の室内配置のいずれとも一致しないことを、人物を交換した場合も含めて照合しました。同じ部屋・同じ配置範囲の中での検証であり、大きく異なる環境への外挿を示すものではありません。[配置の照合](v11_color/reports/round02_layout_separation.json)

4配置×青・赤×2初期条件の16試験／モデルです。開始位置は前後・左右±5cm、向きは±5度。機体のセンサー乱数も試験ごとに固定しました。停止は目標点から25cm以内、水平速度0.08m/s以下を3秒以上。離陸後の静止、旋回後の停止、人物との距離、画像保存、着陸など、既存の他の条件も維持しています。

途中で保存先をE:へ集約しました。移動した全ファイルのハッシュを照合して旧パスを維持し、最後のv1.0／v1.1比較は両方ともE:上の同じ実行系で行っています。以前の開発試験との違いも記録に残しています。[保存先変更の記録](v11_color/protocol/storage_migration_e.json)

`train13_en` は2,000ステップの保存時に、Windowsが既存の再開用ファイルの置き換えを拒否して停止しました。新しい保存ファイルは完全だったため、重み・AdamWの状態・データ抽出とCPU／GPUの乱数状態を復元し、予定どおり計6,000ステップまで続けました。以後の再開用ファイルはステップごとの別名で保存しました。中断前のログと失敗記録は残し、途中の重みを成績で選んだり、評価に使ったりしていません。[保存内容の検査](v11_color/reports/train13_interrupted_save_integrity.json) / [再開前の記録](v11_color/protocol/train13_resume01.json) / [状態の復元確認](v11_color/models/train13_en/resume01_started.json) / [最終ステップの重み・最適化状態・学習回数の照合](v11_color/reports/train13_resume01_completion_audit.json)

`train13_en` の飛行後の出力診断には、最初に一つ前の教師を参照した誤りがありました。正しい教師を参照する版で再計算し、元の診断も残しています。飛行出力や成功・失敗の判定は変えていません。また、当初のソース控えに教師ファイル1点が漏れていたため、学習前の計画に記録したハッシュとの一致を確認して補いました。事後の補完であることも記録しています。[診断の訂正](v11_color/reports/train13_diagnostic_reference_correction.json) / [ソース控えの補完](v11_color/reports/train13_teacher_source_completion_audit.json)

容量確保のため、使用していない過去候補22ファイルにはNTFSの可逆圧縮を適用しました。圧縮前後で全ファイルのSHA-256が一致し、パス・内容を保っています。削除や移動はしていません。提出版v1.0、動画、飛行記録はこの圧縮の対象外です。[候補18ファイルの照合](v11_color/reports/archive_compression/status.json) / [過去候補4ファイルの照合](v11_color/reports/legacy_model_compression/status.json)

その後、記録など354ファイルにも可逆圧縮を行い、全件のハッシュ一致を確認しました。さらにユーザーの承認で、古い紹介映像の再生成可能な連番画像6,060枚と、終了済み学習13件の復旧用ファイルを整理しました。復旧用ファイル内の全パラメーターが保存済みの最終モデルと完全一致することを確認し、乱数状態・学習回数・サンプリング情報は別途保存しています。最適化器の中間状態は削除したため、それを使った厳密な途中再開はできません。全候補の最終重み、成功・失敗を含む全試験記録、提出動画・PDFは残しています。[追加圧縮の照合](v11_color/reports/inactive_record_compression/status.json) / [映像用生成物の整理](v11_color/reports/storage_cleanup_20261030/render_frame_cleanup_result.json) / [最終重みと一致した復旧ファイル10件の整理](v11_color/reports/storage_cleanup_20261030/completed_recovery_cleanup_result.json) / [以前の学習3件の同一確認](v11_color/reports/storage_cleanup_20261030/legacy_recovery_cleanup_result.json)

実行環境を安定させるため、WSL側のシミュレーションを4 CPU・8GiB以下に制限し、優先度を下げて1件ずつ実行しました。旧モデルと新モデルの最終比較には同じ制限を適用しています。過去の `train08_en_capped` は `train08_en` と同一の最終重みを使う評価用の名前で、追加の学習段階ではありません。起動エラーと、利用者の指示で中断した飛行も保存しています。中断した飛行の採点は不成功でしたが、通常の性能試験とは分けています。[資源制限の事前記録](v11_color/protocol/bounded_execution.json) / [同一モデルの対応](v11_color/models/train08_en_capped/evaluation_alias.json) / [中断した飛行](v11_color/runs/dev_train08_en/dev01_blue_v1.1/outcome.json) / [起動・中断を含む一覧](v11_color/ALL_TRIALS.md) / [使用量と起動エラーの集計](v11_color/reports/bounded_execution_summary.json)

| 条件 | v1.0 | v1.1 |
| --- | --- | --- |
{chr(10).join(rows)}

独立な試行と仮定した参考の95% Wilson区間は、v1.0が{s0['wilson95'][0]*100:.1f}–{s0['wilson95'][1]*100:.1f}%、v1.1が{s1['wilson95'][0]*100:.1f}–{s1['wilson95'][1]*100:.1f}%です。同じ部屋の関連した少数試験であり、現場での信頼性を表しません。合格基準は14/16以上、各色7/8以上、各配置3/4以上と、評価前に定めています。[この評価の全実行](v11_color/runs/{final_suite}/summary.json) / [以前の失敗も含む全一覧](v11_color/ALL_TRIALS.md) / [独立した再採点](v11_color/reports/{candidate}_all_records_verified.json)

### 色と指示を入れ替える検査

新しい4配置で各4視点を固定し、服の色だけを交換した32画像を用意しました。同じ画像・同じ機体状態で青と赤の英語指示を切り替えます。先頭10ステップの水平速度の平均が、他方よりも指定対象の目標点の方向に近い場合を正解とし、0.02m/s未満の静止出力や同点も不正解に含めます。

| 指標 | v1.0 | v1.1 |
| --- | --- | --- |
| 指定目標の方向に向いた出力 | {p0['correct_goal']}/{p0['outputs']} | {p1['correct_goal']}/{p1['outputs']} |
| 指定目標の方向との角度差の中央値 | {p0['median_goal_angle_deg']:.2f}度 | {p1['median_goal_angle_deg']:.2f}度 |
| 服色交換×指示交換の4通りすべて正解 | {p0['whole_quartet_correct']}/{p0['quartets']}組 | {p1['whole_quartet_correct']}/{p1['quartets']}組 |

![事前指定した服色交換例と、青・赤の指示に対する水平出力方向](v11_color/figures_round02_english/probe_01.png)

中央・右は上から見た水平面で、矢印の色は指示した色です。向きが分かるよう矢印の長さを揃えており、飛行軌跡や速度の大きさを示すものではありません。図の番号は推論前に指定しました。これは飛行成功率と別の検査であり、関連した画像の組を独立標本とは扱いません。[事前条件](v11_color/protocol/static_probe_round02_english.json) / [全出力](v11_color/probe_round02_english/outputs/raw_outputs.jsonl) / [集計](v11_color/probe_round02_english/outputs/summary.json)

旧T2の両者が写る82画像では、英日併記の正方向出力が161/164、日本語だけでは84/164でした。旧T2は人物中心への方向、今回の主指標は停止目標点への方向であり、数値を直接比較しません。日本語だけでのVLA操作は今回の達成範囲に含めません。[旧T2の全結果](v11_color/prior/T2_summary.json)

### 動画の動作と、既知の失敗の再確認

青・赤への接近、右→左と左だけの旋回、通常視界の青・赤の捜索、薄い霧・濃い霧・粉じんでの青の捜索は、採用モデルで{sum(x['success'] for x in r['regression_cases'])}/{len(r['regression_cases'])}件成功しました。最初に失敗した配置交換の青の捜索も完了しました。これらは回帰確認で、最終評価の16件には加えていません。[回帰確認](v11_color/runs/regression_{candidate}/summary.json) / [旋回などの確認](v11_color/runs/dev_{candidate}/summary.json) / [元の失敗配置の再確認](v11_color/runs/known_failure_{candidate}/summary.json)

最終室内への適応段階と今回の学習画像の描画濃度は0.004、視界条件の評価値は0.06／0.12です。今回の8,408画像は、新規6,000枚が保存済み描画からのJPEG変換と一致し、既存2,408枚が元画像と一致することを照合しました。元のシーンと描画処理のハッシュも確認しています。描画パラメーターでは15～30倍ですが、実際の視程や粒子濃度の倍率ではありません。基盤モデルの事前学習全体が霧を未経験だったとも主張しません。発見はSSDlite＋色判定が担い、VLAはその画像条件での接近・停止などの動作を生成します。[v1.0の確認](v11_color/prior/T6_verified_scope.json) / [v1.1の全学習画像の照合](v11_color/reports/v11_training_visibility_scope.json)

最後の学習段階でも同じ8,408枚を使用しています。画像一覧と各ファイル、描画記録のハッシュを再照合し、上記の確認と同じ画像であることを確かめました。[最終段階の画像との対応](v11_color/reports/v11_training_visibility_train16.json)

### 過去の改善記録と限界

旧記録の青／赤の停止時間は、外観適応前後が0.00／0.00秒→2.97／3.07秒、停止改善前後が2.63／3.87秒→5.75／4.67秒でした。前者では描画版、後者では工程判定も変更しており、追加学習だけの効果を分離した比較ではありません。[数値と元記録のパス](v11_color/prior/T5_existing_records.json) / [過去の採点原票16件](v11_color/prior/T5_source_index.md)

今回も学習設計の各要素の寄与を分離した実験ではありません。最初の英日併記の評価と、英語へ統一した最終評価は別々に報告しています。確認範囲は同じ部屋・同じ2人の外見・静止人物・限定した配置範囲です。未知の部屋、動く人物、任意の服の色、複数室、実機での飛行は未検証です。

### 役割分担

| 担当 | 役割 |
| --- | --- |
| 任務管理 | 工程の順序、完了判定、再旋回・再捕捉・時間切れを管理 |
| SSDlite＋色判定 | 人物と服の色を判定し、連続3画像で発見を確認 |
| SmolVLA | 現在の画像・英語の工程指示・機体状態から、6成分の動作列を生成 |
| 変換＋ArduPilot | 速度を姿勢目標へ変換して安定化。指令の上限は水平速度0.2m/s・旋回速度0.35rad/s |

上位の「青い服の人を探して」はVLAへ直接渡さず、任務管理が `Approach the person wearing blue and stop.` などの工程指示へ切り替えます。任意の文章から任務全体を計画する機能ではありません。

今回の実装では過去の画像列や任務履歴をVLAに入力せず、工程の進み具合は任務管理が持ちます。発見は独立した検出器で確認し、動作生成と確認を分離しています。検出器も誤る可能性があり、誤接近を必ず防ぐ保証ではありません。正解の座標は教師データ作成、描画・センサー合成、飛行後の採点に限って使い、実行中のVLA・人物判定・任務管理へ渡していません。

根拠：[任務管理](v11_color/runtime_english/search_mission.py) / [人物・服色の判定](v11_color/runtime_english/perception.py) / [連続画像での確認](v11_color/runtime_english/confirmation.py) / [VLAへの入力](v11_color/runtime_english/search_worker.py) / [動作列の実行と上限](v11_color/runtime_english/search_link.py)。[役割とコードの対応](v11_color/reports/runtime_role_source_audit.json)には該当箇所とハッシュを記録しました。入力境界の構文確認と実装の読解であり、あらゆる情報経路の形式的な証明ではありません。

'''
# Lead with the problem, role boundaries and final evidence. Keep the full
# development history available without making readers traverse every attempt.
parts=section.split('\n### ')
intro=parts[0]
sections={part.split('\n',1)[0]:part.split('\n',1)[1] for part in parts[1:]}
assert len(sections)==7
history_title='弱点の発見と、失敗した評価を残す'
problem,history_body=sections[history_title].strip().split('\n\n',1)
evaluation_title='新しい配置での最終評価（英語の指示）'
evaluation=sections[evaluation_title]
ops_start=evaluation.index('途中で保存先をE:へ集約しました。')
ops_end=evaluation.index('| 条件 | v1.0 | v1.1 |')
operations=evaluation[ops_start:ops_end].strip()
sections[evaluation_title]=evaluation[:ops_start]+evaluation[ops_end:]
section=intro+'\n### 配置を変えて分かった弱点\n\n'+problem+'\n\n'
for title in ['役割分担',evaluation_title,'色と指示を入れ替える検査','動画の動作と、既知の失敗の再確認','学習データとモデル','過去の改善記録と限界']:
    section+='### '+title+'\n'+sections[title].strip()+'\n\n'
section+='<details>\n<summary>改善の経緯と、採用しなかった候補の全結果</summary>\n\n'+history_body+'\n\n</details>\n\n'
section+='<details>\n<summary>実行環境・保存先の変更と記録の保全</summary>\n\n'+operations+'\n\n</details>\n\n'
assert text.count('## 実機への展開')==1
text=text.replace('## 検証結果','## 提出済み動画の検証結果（v1.0）',1).replace('## SmolVLAの追加学習','## 動画のモデル（v1.0）の追加学習',1)
text=text.replace('## 実機への展開',section+'## 実機への展開',1)
banner='\n\n動画は提出時のv1.0のままです。v1.1の追加学習・英語の指示による比較検証と、途中の失敗も追記しました。\n\n[説明PDF（4ページ）](docs/説明資料_v1.1.pdf) / [全試験一覧](v11_color/ALL_TRIALS.md) / [公開する記録の範囲と再採点](v11_color/PUBLICATION_SCOPE.md)\n'
text=text.replace('# 災害救助ドローン','# 災害救助ドローン'+banner,1)
out=W/'reports/README_v1.1_review.md';out.write_text(text,encoding='utf-8')
(W/'reports/readme_provenance.json').write_text(json.dumps(dict(original_readme_sha256=sha(source),candidate_sha256=sha(out),public_checkout_modified=False,publication_approved=False,result_sha256=sha(W/'results/all_trials_round02_english.json')),indent=2),encoding='utf-8')
print(out)
