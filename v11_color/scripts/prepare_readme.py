"""Prepare a review copy, leaving the public checkout and Git untouched."""
import json,hashlib
from pathlib import Path
from training_history import lineage
W=Path(__file__).resolve().parents[1];P=W.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
r=read(W/'results/all_trials.json');selected=read(W/'protocol/selected_final.json');probe=read(W/'probe/outputs/summary.json')
exposure=read(W/'models'/selected['candidate']/'sampling_exposure.json')
history=lineage(W,selected['candidate']);steps=' + '.join(f"{h['steps']:,}" for h in history)
assert r['preregistered_goal_met'],'Do not describe an unsuccessful candidate as an improvement that met the goal'
assert len([x for x in r['all_executed_cases'] if x['suite'].startswith('heldout')])==32
source=Path('C:/Temp/pai2026_submission/pai2026/README.md');text=source.read_text(encoding='utf-8')
def stat(version,group='all',key=None):return next(s for s in r['heldout_statistics'] if s['model']==version and s['group']==group and s['key']==key)
def number(s):return f"{s['k']}/{s['n']}（{100*s['k']/s['n']:.1f}%）"
def probe_stat(version,group):return next(s for s in probe['summary'] if s['model']==version and s['prompt_group']==group)
a,b=stat('v1.0'),stat('v1.1');rows=[]
for group,key,label in [('all',None,'全16試験'),('color','blue','青い服への指示'),('color','red','赤い服への指示')]:rows.append(f"| {label} | {number(stat('v1.0',group,key))} | {number(stat('v1.1',group,key))} |")
for key in ['heldout01','heldout02','heldout03','heldout04']:rows.append(f"| 配置 {key[-2:]} | {number(stat('v1.0','layout',key))} | {number(stat('v1.1','layout',key))} |")
prows=[]
for group,label in [('runtime_bilingual','本番と同じ英日併記'),('japanese','日本語のみ')]:
    p0,p1=probe_stat('v1.0',group),probe_stat('v1.1',group)
    prows.append(f"| {label} | {p0['correct_goal']}/{p0['outputs']} | {p1['correct_goal']}/{p1['outputs']} | {p1['whole_quartet_correct']}/{p1['quartets']} |")
role='''| 担当 | 実際の役割 |
| --- | --- |
| 任務管理 | 工程の順序、完了判定、再旋回・再捕捉・時間切れを管理 |
| SSDlite＋色判定 | 人物と服の色を判定し、連続3画像で発見を確認 |
| SmolVLA | 現在の画像・工程の指示・9成分の機体状態から、速度・旋回・離着陸要求の6成分を32ステップ分生成 |
| 変換＋ArduPilot | 速度を姿勢目標へ変換し、姿勢を安定化。水平速度は0.2m/s、旋回速度は0.35rad/sを上限とする |

上位の「青い服の人を探して」はVLAに直接渡しません。任務管理が、例えば「Approach the person wearing blue and stop. 青い服の人の前で止まって。」という**英日併記の工程指示**へ切り替えます。自由な文章を解釈して任務全体を計画する機能ではありません。

今回のVLAには過去の画像列や任務履歴を入力していないため、工程の進み具合は任務管理が保持します。発見は独立した検出器で確認し、動作生成と確認を分離しています。ただし検出器も誤る可能性があり、誤接近を必ず防ぐという保証ではありません。
'''
section=f'''## v1.1：配置への依存を調べ、追加学習で改善する

**公開済み動画はv1.0で撮影したもので、変更していません。** 以下は動画の撮影後に追加した検証です。提出時のコードと記録は[Release v1.0.0](https://github.com/curio184/pai2026/releases/tag/v1.0.0)に残します。

### v1.0で見つかった弱点

青と赤の立ち位置を交換した試験で、v1.0は対象を見失い、再捕捉が時間切れになりました。青の目標点への最短距離は1.218m、赤の目標点へは0.204mでした。これは人物そのものとの距離ではなく、各人物の前0.9mにある採点用目標点への距離です。位置への依存を示唆する失敗であり、「位置しか使っていなかった」と断定するものではありません。[失敗記録](validation/v1.1/prior/T3_failure_analysis.json)

同じ画像の指示だけを替えた旧T2では、両者が写る82枚に対して、指定人物の方向により近い出力は本番の英日併記で161/164、日本語のみでは84/164でした。この検査だけでは、色と言葉を位置に結び付けて覚えた可能性を除けません。[旧T2の全結果](validation/v1.1/prior/T2_summary.json)

v1.1では、元のT3の失敗配置も同じ条件で再確認し、一連の捜索を完了しました。これは既知の失敗を再確認した1回の結果であり、未知条件での成功率とは区別します。[再確認の記録](v11_color/runs/known_failure_{selected['candidate']}/T3_blue_retest_v1.1/record/search_score.json)

### 変えたもの・固定したもの

同じ室内で20通りの人物配置を用意し、同じ人物・同じ位置・同じカメラ・同じ機体状態のまま、服の色だけを交換した2,000組、4,000枚を作りました。同じ画像に青と赤の指示を対応付ける組も使います。接近時に一人だけが見える視点を含め、既存の2,408枚を保持して離着陸・旋回も復習させています。日本語のみ・英語のみの指示も追加学習に含めました。

この枚数は生成・保持したデータの数です。最後の学習段階で抽出された画像は、新規{exposure['unique_new_images']:,}枚・既存{exposure['unique_retention_images']:,}枚、重複を含む教師例の使用回数は{exposure['total_samples']:,}回です。画像ごとの使用回数と動作・言語の内訳も保存しています。[使用データの記録](v11_color/models/{selected['candidate']}/sampling_exposure.json)

採用モデルへの追加学習は {steps} ステップです。最初の候補は開発試験8件中4件の成功に留まりました。そこで、目標付近の学習例と従来配置の接近・停止の例を多く抽出し、水平速度0.26m/sまでの機体状態も追加しました。この段階では画像と教師の制御則は変更していません。[初回候補の全結果](v11_color/runs/dev_train01/summary.json) / [停止精度に向けた学習条件](v11_color/protocol/train02.json)

次の候補は7/8件成功しましたが、1件で停止後の報告・着陸中に人物へ近づき、最小距離が0.433mとなって既存の0.45m基準を下回りました。そこで、教師が教える停止位置を人物の前0.9mから1.0mへ10cm手前に移しました。採点は元の0.9mの目標点・25cm以内・3秒以上のままで、制御器や最小距離の基準も変えていません。これは着陸までの余裕を学習するための変更です。開発・最終評価の画像は全段階を通じて学習に使わず、最終評価は開発段階を終えてから実行しました。[2番目の候補の全結果](v11_color/runs/dev_train02/summary.json) / [教師の停止位置の変更](v11_color/protocol/train03.json)

画像エンコーダーを固定し、動作生成部とテキスト層の一部を追加学習しました。最終ステップの重みを使い、途中の重みを評価成績で選んでいません。任務管理・検出器・制御ゲイン・成功判定は同じです。開始姿勢を変える専用ラッパーだけを分離し、比較する両モデルに同じ初期条件とセンサー乱数シードを与えました。[事前登録](validation/v1.1/protocol/plan.json) / [学習記録](validation/v1.1/training/result.json)

最終モデルSHA-256：`{selected['checkpoint_sha256']}`

### 未学習配置での飛行比較

開発確認用2配置とは別に、未学習の4配置×青・赤の2指示×2種類の開始条件、計16試験を各モデルで実行しました。開始位置は前後・左右±5cm、向きは±5度の範囲です。配置・乱数・判定条件を先に保存し、成功・失敗を全件集計しました。停止条件は目標点から25cm以内、水平速度0.08m/s以下を3秒以上で、その他の既存判定も維持しています。

| 条件 | v1.0 | v1.1 |
| --- | --- | --- |
{chr(10).join(rows)}

参考として、独立な試行を仮定した95% Wilson区間は、v1.0が{a['wilson95'][0]*100:.1f}–{a['wilson95'][1]*100:.1f}%、v1.1が{b['wilson95'][0]*100:.1f}–{b['wilson95'][1]*100:.1f}%です。同じ室内の関連した少数試験であり、任意の環境での信頼性を意味しません。[全試験・失敗を含む一覧](validation/v1.1/results/all_trials.json)

### 色と指示を切り替える検査

未学習の4配置でカメラ視点を4通り固定し、それぞれ服の色だけを交換しました。32枚について、画像と機体状態を固定して青・赤の指示を入れ替えています。水平動作の先頭10ステップ平均が、他方より指定対象の目標点の方向に近い場合を正解としました。0.02m/s未満の出力や同点は不正解に含めています。

| 指示の表記 | v1.0の正方向出力 | v1.1の正方向出力 | v1.1：服交換と指示交換の4通りすべて正解 |
| --- | --- | --- | --- |
{chr(10).join(prows)}

これは飛行の成功率とは別の、同一入力に対する介入検査です。関連した画像の組なので独立標本として扱いません。旧T2は人物中心への方向、今回の主指標は停止目標点への方向であり、両検査の数値を直接比較しません。[事前条件](validation/v1.1/protocol/static_probe.json) / [全出力](validation/v1.1/probe/raw_outputs.jsonl) / [集計](validation/v1.1/probe/summary.json)

![事前に指定した服色交換例と、青・赤の指示に対する出力方向](v11_color/figures/probe_01.png)

本番の英日併記について、正方向60/64以上、4通りすべて正解14/16組以上を、v1.1の推論・飛行評価より前に完了基準として記録しました。日本語のみの結果も全件掲載し、本番と同じ条件の結果とは分けています。[追加の完了基準](v11_color/protocol/completion_addendum.json)

### 動画に登場する動作の確認

v1.1について、青・赤への接近、右→左の旋回、左旋回、通常視界の青・赤の捜索、薄い霧・濃い霧・粉じんでの青の捜索を確認しました。結果は{sum(x['success'] for x in r['regression_cases'])}/{len(r['regression_cases'])}件成功です。動画そのものはv1.0の記録であり、v1.1の映像へ置き換えたものではありません。

最終室内への適応段階と今回の合成画像の描画濃度は0.004。評価時の0.06・0.12はこの描画パラメーターの15～30倍です。実際の粉じん濃度・視程の倍率ではなく、基盤モデルの事前学習全体が霧を未経験だったという意味でもありません。人物の発見はSSDlite＋色判定が担い、VLAの役割として確認したのは、その画像条件での接近・停止などの動作生成です。

### 過去の改善記録と今回の主張の範囲

旧記録の青／赤の停止継続時間は、外観への追加学習前が0.00／0.00秒、追加学習後が2.97／3.07秒でした。停止改善前は2.63／3.87秒、改善後のv1.0は5.75／4.67秒です。ただし外観の比較では描画版が異なり、停止改善の比較では工程判定も変更されています。追加学習だけの効果を分離した比較ではありません。[数値と元記録のパス](validation/v1.1/prior/T5_existing_records.json)

今回のv1.0とv1.1の比較では制御器を固定しましたが、学習設計の各要素の寄与を分離する実験ではありません。また、評価は同じ部屋・同じ2人の外見・静止した人物・限定した配置範囲に留まります。未知の部屋、動く被災者、任意の服の色、複数室、実機飛行は未検証です。

### 役割分担

{role}

'''
text=text.replace('## 検証結果','## 提出済み動画の検証結果（v1.0）',1)
text=text.replace('## SmolVLAの追加学習','## 動画のモデル（v1.0）の追加学習',1)
text=text.replace('## 実機への展開',section+'## 実機への展開',1)
text=text.replace('validation/v1.1/','v11_color/').replace('v11_color/training/result.json',f"v11_color/models/{selected['candidate']}/result.json").replace('v11_color/probe/raw_outputs.jsonl','v11_color/probe/outputs/raw_outputs.jsonl').replace('v11_color/probe/summary.json','v11_color/probe/outputs/summary.json')
banner='\n\nこの更新案には、提出後に見つかったv1.0の配置変更時の失敗と、v1.1の追加学習・比較検証を追記しています。動画はv1.0のままです。\n'
banner+='\n[説明PDF（v1.1・4ページ）](docs/説明資料_v1.1.pdf) / [追加検証の全実行](v11_color/ALL_TRIALS.md) / [公開する記録の範囲と再採点手順](v11_color/PUBLICATION_SCOPE.md)\n'
text=text.replace('# 災害救助ドローン','# 災害救助ドローン'+banner,1)
out=W/'reports/README_v1.1_review.md';out.write_text(text,encoding='utf-8')
(W/'reports/readme_provenance.json').write_text(json.dumps(dict(original_readme_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),candidate_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),public_checkout_modified=False,publication_approved=False),indent=2))
print(out)
