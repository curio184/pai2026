"""Create a review README only after all frozen goal/evidence gates pass."""
import json,hashlib,argparse
from pathlib import Path
from training_history import lineage
from navfocus_labels import LABELS
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--review-incomplete',action='store_true');args=parser.parse_args()
    r=read(W/'results/all_trials_navfocus.json')
    assert r['completed']==42 and r['all_new_records_independently_rescored'] and r['probe_arithmetic_and_images_verified']
    assert r['preregistered_goal_met'] or args.review_incomplete,'Do not substitute a failure report for goal completion'
    review=not r['preregistered_goal_met']
    plan=read(W/'protocol/navfocus_final.json');probe=read(W/'probe_navfocus/outputs/summary.json')
    history=lineage(W,plan['candidate'])
    def stat(model,g='all',k=None):return next(s for s in r['heldout_statistics'] if s['model']==model and s['group']==g and s['key']==k)
    def count(s):return f"{s['k']}/{s['n']}"
    def ps(model):return next(s for s in probe['summary'] if s['model']==model and s['prompt_group']=='runtime_english')
    a,b=ps('v1.0'),ps('v1.1')
    acceptance_note='**固定検証の合格条件は未達です。** 以下は結果を確認するための原稿で、ゴール達成済みの更新版ではありません。' if review else '**事前に固定した検証の合格条件を満たしました。**'
    rows=[]
    for g,k,name in [('all',None,'全試験'),('color','blue','青い服への指示'),('color','red','赤い服への指示')]+[('layout',s['name'],s['name']) for s in read(W/'protocol/navfocus_layouts.json')['heldout_layouts']]:
        rows.append(f"| {name} | {count(stat('v1.0',g,k))} | {count(stat('v1.1',g,k))} |")
    training_rows=[]
    for h in history:
        p=next(p for p in (W/'protocol').glob('*.json') if sha(p)==h['plan_sha256'])
        training_rows.append(f"| {h['candidate']} | {h['steps']:,} | `{h['checkpoint_sha256']}` | [条件](v11_color/protocol/{p.name}) / [完了記録](v11_color/models/{h['candidate']}/result.json) |")
    regression_rows=[]
    for row in r['regression_cases']+r['known_failure_cases']:
        regression_rows.append(f"| {LABELS.get(row['case']['id'],row['case']['id'])} | {'成功' if row['success'] else '失敗'} | [採点結果](v11_color/{row['score_path']}) |")
    failure_report=read(W/'reports/navfocus_failure_details.json');assert failure_report['completed']==42
    failure_rows=[]
    for row in failure_report['failures']:
        target=row['target'];e=row['evidence'];case=row['case']
        hold='—' if target is None else f"{target['hold_s']:.2f}秒"
        image='—' if e is None else f"[最後の接近入力](v11_color/{e['image']})"
        failure_rows.append(f"| {case['id']} / {case['model']} | {hold} | {image} | [記録](v11_color/{row['record']}/outcome.json) |")
    t5=read(W.parent/'validation_v1_1/results/T5_existing_records.json')
    intro=f'''# 災害救助ドローン

言葉による指示で捜索を任せ、操縦の負担を減らす。SmolVLAがカメラ画像から指定された色の人物を選び、接近・停止する動作を生成します。

**公開済み動画はv1.0の記録で、変更していません。** 以下は撮影後の追加検証です。提出時のコードは[Release v1.0.0](https://github.com/curio184/pai2026/releases/tag/v1.0.0)に保存しています。v1.1.0は公開前のレビュー用です。

## v1.1の検証

{acceptance_note}

事前の合格条件は、未学習配置の全体14/16以上・各色7/8以上・各配置3/4以上、動画の9場面すべて、既知の失敗配置1件、静止画像の方向60/64以上・服色と指示の4通りすべて正解14/16組以上です。各飛行の停止条件も含め、結果を見て基準を変更していません。

目指したのは「VLAが人を認識し、近づき、止まる」ことです。ここでの認識は、画像と言葉に応じて指定された人へ向かう動作として検証しています。VLAが別途人物検出ラベルを出力する構成ではありません。

人物配置を交換した試験で、v1.0は青い服の人を見失いました。採点用目標点への最短距離は、青1.218mに対し、元の青の位置にいる赤0.204mでした。人物そのものの距離ではなく、人物の前0.9mの目標点への距離です。位置への依存を示唆しますが、内部で何を記憶したかを断定するものではありません。[元の失敗と分析](v11_color/prior/T3_failure_analysis.json)

服の色と配置の結び付きを崩す教師データで学習し直し、離陸・定角旋回・着陸と飛行の安定化は通常の制御へ分離しました。人物の選択・接近・減速・停止はVLAが担います。学習に使っていない4配置・2色・2開始条件で、v1.0は{count(stat('v1.0'))}、v1.1は{count(stat('v1.1'))}件成功しました。

| 条件 | v1.0 | v1.1 |
| --- | --- | --- |
{chr(10).join(rows)}

同じ条件を対にすると、両モデル成功は{r['paired_outcome_counts']['both_success']}件、新版のみ成功は{r['paired_outcome_counts']['v11_only']}件、旧版のみ成功は{r['paired_outcome_counts']['v10_only']}件、両モデル失敗は{r['paired_outcome_counts']['both_failure']}件です。少数の同室試験であり、一般的な優位性や統計的有意差を主張するものではありません。

配置、開始位置±5cm・向き±5度、乱数、回数、モデル、成功基準は実行前に記録しました。両モデルに**同じ新版の制御器と英語の工程指示**を使っています。v1.0は英日併記で学習しており、言語への適応の影響は分離していません。動画の旧制御器との違いを学習だけの効果とは扱いません。成功率は同じ部屋・同じ2人・限定した配置の結果で、任意の環境での信頼性ではありません。

- [事前登録した42件と合格基準](v11_color/protocol/navfocus_final.json)
- [全試験の一覧（失敗を含む）](v11_color/ALL_TRIALS_NAVFOCUS.md)
- [数値の全件集計](v11_color/results/all_trials_navfocus.json)
- [保存記録の独立再採点](v11_color/reports/navfocus_records_verified.json)

停止の基準は**目標点から25cm以内・水平速度0.08m/s以下を3秒以上**。離陸後の静止、旋回、人物との距離、確認画像保存、着陸・モーター停止の物理条件も保持しました。離着陸要求の出所だけは新しい分担に合わせて判定します。旧来の「VLAによる離着陸要求」を必須とする判定結果も `physical_score_original_contract.json` に保存し、隠していません。新判定では接近の4成分がVLA出力と一致し、新しいVLA停止指令で接近を完了したことも要求します。途中の重みや成功した実行だけを選んでいません。

停止時間には接近後の画像保存・着陸工程を含めません。採点した停止区間のうち、VLAの動作が採用されている連続区間だけでも3秒以上あることを、成功した人物接近の全件で確認しました。工程切り替えと20Hzの制御更新の間に生じる行は、この追加の照合から除外しています。

### 成功しなかった試験

| 試験 / モデル | 目標範囲内の停止 | VLA入力 | 記録 |
| --- | --- | --- | --- |
{chr(10).join(failure_rows)}

表は固定試験で失敗した全件です。停止時間は距離・速度・高度の条件が同時に成立した時間であり、静止していても目標範囲外なら合格しません。失敗した工程、満たさなかった条件、最後の接近入力と動作は[失敗の全件分析](v11_color/reports/navfocus_failure_details.json)に保存しています。結果に応じた追加試行や係数変更は行っていません。

## 本当に画像と言葉で相手を選ぶか

32画像について、同じ画像・機体状態のまま指示を青／赤へ替えました。さらに服色だけを交換した画像と組にし、16組の「服色2通り×指示2通り」を調べました。もう一方の目標よりも、指示した目標の方向に近いVLA出力はv1.0 {a['correct_goal']}/{a['outputs']}、v1.1 {b['correct_goal']}/{b['outputs']}。角度差の中央値は{a['median_goal_angle_deg']:.1f}度／{b['median_goal_angle_deg']:.1f}度。4通りすべて正解はv1.1 {b['whole_quartet_correct']}/{b['quartets']}組でした。

![事前指定した画像での色・指示交換](v11_color/figures_navfocus/probe_01.png)

矢印は制御器を通す前のVLAの先頭10ステップの平均水平速度の向きで、表示の長さは統一しています。速度0.02m/s未満と同点は不正解。人物方向・目標方向は推論後に真値から計算し、モデルには渡していません。この検査は関連した静止画像の組であり、飛行成功率とは区別します。[事前条件](v11_color/protocol/static_probe_navfocus.json) / [全出力](v11_color/probe_navfocus/outputs/raw_outputs.jsonl) / [集計](v11_color/probe_navfocus/outputs/summary.json) / [画像・計算の照合](v11_color/reports/probe_navfocus_verified.json)

動画モデルの既存検査では、両者が写る82画像に対し、英日併記の指示で161/164、日本語だけで84/164でした。既知画像での検査で、配置交換に強い証拠ではありません。今回の英語・未学習配置の結果と合算しません。[v1.0の言語交換検査](v11_color/prior/T2_summary.json)

## VLAと制御器の役割

| 担当 | 実行すること |
| --- | --- |
| 任務管理 | 離陸→静止→見回し→発見確認→接近→画像保存→着陸の順序、工程の完了判定、再捕捉・再旋回・時間切れ |
| SSDlite＋色判定 | 人物検出と服の色を判定し、連続3画像で発見を独立に確認。接近先への速度は生成しない |
| SmolVLA | 現在の画像・英語の工程指示・推定機体状態から、速度・旋回・離着陸要求の6成分を32ステップ分生成 |
| 通常の制御＋ArduPilot | 離陸・定角旋回・着陸を実行し、速度・姿勢を安定化。人物の選択や人物に対する接近・停止は行わない |

上位の「青い服の人を探して」はVLAに直接入りません。任務管理が `Approach the person wearing blue and stop.` などの工程指示へ切り替えます。VLAには過去の画像列や任務履歴を入力しないため、画像に現れない進行状況を任務管理が保持します。発見を独立した検出器で確認することで、動作生成とは別に対象を確認できます。誤認や誤接近を必ず防ぐ保証ではありません。

VLAの入力は320×240のRGB画像、指示、9成分の推定機体状態です。**人物の正解座標・距離・検出枠は入力しません。** `search_worker.py` は先にVLAを推論し、その後にSSDliteで同じ画像を判定します。真値は教師データの作成、描画・センサー合成、飛行後の採点だけに使います。[入力と検出の分離](v11_color/runtime_navfocus/search_worker.py) / [VLA入力](v11_color/runtime_navfocus/smolvla_policy.py) / [任務管理](v11_color/runtime_navfocus/search_mission.py)

### v1.1で変更した制御

接近工程では、前後・左右・上下・旋回の4成分をVLA由来の指令として採用し、所定の上限を適用して速度・姿勢制御へ渡します。水平速度は0.2m/s以下、旋回速度は0.35rad/s以下です。検出器が別の人物誘導指令に置き換えることはありません。離陸・定角旋回・着陸では通常の制御が高度や角度の目標を追い、水平速度の要求はゼロにします。**VLAの6成分すべてを常にそのまま実行しているわけではありません。** モデルの出力、工程による採用指令、上限処理後の水平速度要求と、それぞれの出所を保存しています。[基本動作の実装](v11_color/runtime_navfocus/flight_primitives.py)

速度制御はPI制御（比例1.0、積分0.25）、積分補正は推定NED座標で保持し、旋回に追従して機体座標へ変換します。加速度は各軸±0.8m/s²、積分補正の大きさは0.8m/s²に制限します。人物座標、画像、検出枠は使いません。これは位置へ誘導する別の画像制御器ではなく、VLAの速度要求に追従する制御です。[実装](v11_color/runtime_navfocus/velocity_stabilizer.py)

接近完了には従来の停止指令窓（4秒・0.065m/s以下）、推定速度、独立した対象確認を用います。短い `stale_hover` が続く間は最大0.5秒だけ前の停止意図を記憶しますが、古い動作を実行することはありません。完了時には新しい一致した指示の出力が必要です。2.5秒の鮮度条件と8秒のウォッチドッグは維持しています。[停止意図の扱い](v11_color/runtime_navfocus/stop_intent.py) / [実際の出力と実行の照合](v11_color/reports/navfocus_execution_audit.json)

基本動作の高度補正は比例0.8・上昇速度の減衰0.4、定角旋回は角度誤差の比例0.8・旋回速度の減衰0.4で、旋回指令は0.25rad/s以下です。接近中にこれらの基本動作制御がVLAの4成分を置き換えることはありません。新構成の飛行前に固定し、結果を見て係数を再調整していません。[コードの固定記録](v11_color/protocol/runtime_navfocus_lock.json) / [入力と役割の確認](v11_color/reports/navfocus_role_source_audit.json)

水平安定化だけを分離した一つ前の構成 `control_v11` は8件で終了しました。新版4件はいずれも接近前の時間切れで、旧版4件も失敗でした。残る34件は構成変更のため未実行と明記し、成功率の分母には入れません。この診断に使った配置を最終評価から分け、新しい4配置を同じ範囲から無選別で生成して固定しました。モデルの追加学習は行っていません。[旧構成8件と中止の記録](v11_color/runs/control_v11_final/batch_closed.json) / [新しい配置の事前条件](v11_color/protocol/navfocus_layouts.json)

記録の `controller_source_modified: false` はArduPilot本体のソースを指し、Python側の制御が旧版と同じという意味ではありません。`flight_adapter_revision: navfocus` が今回の分担を識別します。

## 動画の機能を保持できたか

動画の9場面と、v1.0が失敗した既知の配置1件を同じ最終モデルで確認しました。

| 場面 | 結果 | 記録 |
| --- | --- | --- |
{chr(10).join(regression_rows)}

通常・薄い霧・濃い霧・粉じんの4条件を含みます。学習画像の描画濃度は0.004、評価条件は0.06・0.12・0.12でした。描画パラメーターとして15〜30倍であり、実際の視程や粒子濃度の倍率ではありません。発見確認はSSDlite、視界不良の画像からの接近・停止の動作生成はVLAの役割です。[学習画像の全ハッシュと濃度確認](v11_color/reports/v11_training_visibility_train16.json) / [視界条件](v11_color/prior/T6_verified_scope.json)

## 学習と検証の記録

v1.0の記録と重みは保存し、v1.1は別モデルです。同室の20配置で服色を交換した3,000組・6,000画像を作り、既存2,408画像も保持しました。色の学習では画像エンコーダーを固定し、動作生成部と一部のテキスト層を更新。その後の減速・旋回の学習では画像・言語の重みを固定しました。最後の学習は6,000ステップ。最終モデルの全学習パラメーターが最終ステップの保存値と一致することを確認しています。

複数の候補と既知配置での開発を経ています。初期の最終評価は旧モデル2/16、候補6/16で失敗し、その配置を以後の開発に使用しました。今回の4配置は別途事前に固定し、教師データに入れていません。全候補・途中の失敗を残し、異なる候補の成功数を合算した成功率は示しません。

| 学習段階 | ステップ | 最終モデルSHA-256 | 根拠 |
| --- | --- | --- | --- |
{chr(10).join(training_rows)}

合計{sum(h['steps'] for h in history):,}ステップ・{len(history)}段階です。個々の学習変更や制御変更の寄与を一つずつ分離した実験ではありません。[教師データ監査](v11_color/data/dataset16_en/audit.json) / [最終保存の照合](v11_color/reports/train16_final_checkpoint_completion_audit.json) / [全試験](v11_color/ALL_TRIALS_NAVFOCUS.md)

既存記録を使った外観適応と停止精度の改善比較は、[T5の数値と根拠パス](v11_color/prior/T5_existing_records.json)に掲載しています。描画版や工程判定の同時変更を含み、学習単独の効果ではありません。新たな試行は行っていません。

## 記録の再検証

保存済みの飛行をNumPyで再採点し、画像・指示交換の集計をNumPyとPillowで再計算できます。GPUや新しい推論は不要です。

```sh
python v11_color/scripts/verify_navfocus.py --no-write
python v11_color/scripts/verify_probe_navfocus.py --no-write
```

元の記録は変更しません。公開時に作業パスを匿名化したファイルは、元と配布版のハッシュを `PUBLICATION_PROVENANCE.json` で区別します。新規飛行にはモデル重み、Blenderシーン、対応する実行環境が別途必要です。WSLの本プロジェクト処理は4 CPU・8GiB以下、1件ずつ実行しました。

## 検証範囲

同じ部屋・2人の静止人物・限定した配置と英語の工程指示での検証です。未知の部屋、移動人物、複数室探索、自由な言い換えへの対応、実機飛行は未検証です。StampFlyを基に総質量50gで構成したシミュレーションであり、実機に合わせて実測校正したデジタルツインではありません。

---

## 初回提出版 v1.0

以下は動画撮影時の構成と記録です。上記のv1.1とはモデル・指示言語・Python側の制御が異なります。

'''
    original=Path('<WORK_ROOT>/repository/README.md').read_text(encoding='utf-8').split('\n',1)[1].lstrip()
    (W/('reports/README_navfocus_incomplete_draft.md' if review else 'reports/README_navfocus_review.md')).write_text(intro+original,encoding='utf-8')
    print('Prepared gated README review; no Git checkout modified.')
if __name__=='__main__':main()
