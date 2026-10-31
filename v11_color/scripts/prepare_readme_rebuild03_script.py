"""Prepare a gated README generator with the final execution contract explicit."""
from pathlib import Path
W=Path(__file__).resolve().parents[1]
s=(W/'scripts/prepare_readme_navfocus.py').read_text(encoding='utf-8')
s=s.replace("assert r['preregistered_goal_met'] or args.review_incomplete", "assert r['preregistered_goal_met']")
s=s.replace("review=not r['preregistered_goal_met']", "assert r['publication_evidence_complete']\n    review=False")
for a,b in [('all_trials_navfocus','all_trials_rebuild03'),('navfocus_final','rebuild03_final'),('navfocus_layouts','rebuild_final_layouts'),('probe_navfocus','probe_rebuild03'),('figures_navfocus','figures_rebuild03'),('ALL_TRIALS_NAVFOCUS','ALL_TRIALS_REBUILD03'),('navfocus_failure_details','rebuild03_failure_details'),('navfocus_records_verified','rebuild03_final_execution_verified'),('README_navfocus','README_rebuild03')]:s=s.replace(a,b)
s=s.replace('新判定では接近の4成分がVLA出力と一致し、新しいVLA停止指令で接近を完了したことも要求します。', '新判定では、VLAの動作列から復元した到達先を機体自身の推定状態で追従していることと、新しいVLAの停止計画による完了を要求します。生の水平速度がそのまま実行されたとは扱いません。変換の代数計算も保存記録から独立に検算しました。')
s=s.replace('離着陸要求の出所だけは新しい分担に合わせて判定します。', '離着陸の要求元と、接近指令の生成経路は新しい分担に合わせて照合します。物理的な距離・速度・時間の条件は変更しません。')
s=s.replace('服の色と配置の結び付きを崩す教師データで学習し直し、離陸・定角旋回・着陸と飛行の安定化は通常の制御へ分離しました。人物の選択・接近・減速・停止はVLAが担います。', '服の色と配置の結び付きを崩す教師データで学習し直しました。VLAが対象を選び、接近・減速・停止の動作列を生成し、実行部がその計画に追従します。離陸・定角旋回・着陸と姿勢の安定化は通常の制御へ分離しました。')
s=s.replace('| 通常の制御＋ArduPilot | 離陸・定角旋回・着陸を実行し、速度・姿勢を安定化。人物の選択や人物に対する接近・停止は行わない |', '| 計画の実行部＋ArduPilot | VLAの速度列から到達先を復元し、機体自身の移動を補正しながら追従。離陸・定角旋回・着陸と速度・姿勢の安定化を実行。人物や目標座標は入力しない |')
s=s.replace('v11_color/runtime_navfocus/search_worker.py','v11_color/runtime_rebuild03/search_worker.py').replace('v11_color/runtime_navfocus/smolvla_policy.py','v11_color/runtime_rebuild03/smolvla_policy.py').replace('v11_color/runtime_navfocus/search_mission.py','v11_color/runtime_rebuild03/search_mission.py')
start=s.index('### v1.1で変更した制御')
end=s.index('## 動画の機能を保持できたか',start)
section='''### VLAの計画を、動いている機体で実行する

画像を撮ってから指令を実行するまでにも機体は動きます。0.2m/sなら1秒で20cm進むため、停止範囲25cmに対して無視できません。動作列の先頭を受信時から実行するだけの変更は、同条件16件でv1.1が0/16となりました。この失敗を残し、単に更新頻度を上げるだけではなく、画像の古さと実行位置のずれを扱い直しました。[旧方式42件](v11_color/results/all_trials_receipt.json)

今回の実行部は、VLAが出した32ステップの速度列と撮影時の機体状態から、教師の動作定義に従って到達先を復元します。撮影後の移動量を機体自身の推定速度・姿勢の履歴で補正し、現在位置から計画に追従します。**生のVLAの水平速度をそのまま実行する方式ではありません。** 到達先と停止の意図の情報源はVLAであり、人物の正解座標・検出枠・色判定の位置から代わりの誘導指令を作る処理はありません。

- 復元：教師の一次応答を使って速度列を展開し、後半の非飽和指令から残りの移動を推定。非飽和値がない場合は展開終端を使います。教師の距離比例1.4・速度減衰0.5という動作定義を利用しており、任意のVLA出力へ無条件に適用できる変換ではありません。
- 追従：復元した到達先を係数0.5で平滑化し、`0.8 × 残りの移動量 − 0.5 × 推定水平速度` で速度指令を計算。水平速度の大きさは0.2m/s以下、VLAの旋回速度は0.35rad/s以下です。
- 停止：新しいVLA動作列の後半が停止を示し、復元先との差0.08m未満・推定速度0.05m/s未満の状態を従来の停止窓で確認します。これとは別に、飛行後の真値で25cm・0.08m/s・3秒以上を採点します。
- 低位制御：20Hzの速度PI制御とArduPilotで安定化します。PIの比例1.0・積分0.25、加速度各軸±0.8m/s²の制限は維持しています。離陸・定角旋回・着陸は通常の制御が担当します。

[到達先の復元](v11_color/runtime_rebuild03/plan_endpoint.py) / [撮影後の移動補正と追従](v11_color/runtime_rebuild03/plan_tracker.py) / [速度制御](v11_color/runtime_rebuild03/velocity_stabilizer.py) / [生出力と実行指令の照合](v11_color/reports/rebuild03_final_execution_verified.json)

`raw_model_action` と `model_action` はモデルの生出力、`adopted_action` は実行部が採用した指令です。接近中は `execution_owner=VLA_plan_tracker` として、復元に使った動作列、撮影時刻、自機の移動、変換後の速度を保存します。旧判定と新しい経路の判定はどちらも保存しています。

### 画像更新の頻度と、画像の古さを分けて測る

撮影と推論を並行させ、待ち画像は最新の1枚だけにしました。推論の反復回数は10から5へ変更しました。先に定めた12枚の既存画像で、到達先の差の最大値が2.5cm以内かつ停止の解釈が全件一致する、という選択基準を登録して比較しました。5回は最大差1.34cmで採用、2回は4.08cmで不採用。モデルの重み、動作列の長さ32、描画品質は変えていません。[事前条件](v11_color/protocol/flow_steps_benchmark01.json) / [全結果](v11_color/reports/flow_steps_benchmark01.json)

同じ開発条件NFH06での結果です。画像経過時間は、VLAの指令が採用された制御時刻と画像取得時刻との差です（古い画像による待機行は除外）。全件を残し、同時に変えた処理の寄与を個別に証明する比較とは扱いません。

| 構成 | 更新間隔の中央値 | 実行時の画像経過時間の平均 | 目標範囲内の停止 | 任務全体 |
| --- | --- | --- | --- | --- |
| 受信後に動作列の先頭から実行 | 0.87秒 | 1.39秒 | 2.37秒 | 失敗 |
| 到達先追従・撮影と推論を直列処理 | 1.33秒 | 1.88秒 | 4.07秒 | 失敗 |
| 到達先追従・並行処理・推論10回 | 0.62秒 | 1.98秒 | 4.67秒 | 失敗 |
| 到達先追従・並行処理・推論5回 | 0.46秒 | 1.16秒 | 8.64秒 | 成功 |

更新の頻度だけ上がっても、実行時の画像が新しくなるとは限りません。2.5秒の鮮度条件、8秒のウォッチドッグ、電池と物理モデルは変更していません。[同一条件の全記録](v11_color/reports/rebuild_latency_same_case.json)

開発中の失敗も全件を保存しました。到達先追従の初期構成は10件中7件成功、並行処理だけでは次の診断1件が失敗、推論5回の構成では捜索4件が成功しました。基本動作の診断1件は起動先の取り違えで旧10回設定だったため、その事実を保存し、意図した5回設定でも1件確認して成功しました。最終試験では両モデル・全場面とも5回を明示的に検査しています。[起動設定の訂正](v11_color/protocol/rebuild03_primitive5.json)

途中で止めたバッチの未実行分は、成功率の分母に含めません。実行済みの失敗を取り除くこともありません。[開発バッチの終了記録](v11_color/runs/rebuild01_expanded/batch_closed.json) / [全実行](v11_color/ALL_TRIALS_REBUILD03.md)

'''
s=s[:start]+section+s[end:]
s=s.replace('python v11_color/scripts/verify_navfocus.py --no-write','python v11_color/scripts/verify_rebuild03.py --no-write')
s=s.replace('```sh\npython v11_color/scripts/verify_rebuild03.py', '```sh\npython -m pip install -r requirements-verify-v1.1.txt\npython v11_color/scripts/verify_rebuild03.py')
s=s.replace('学習画像の描画濃度は0.004', '今回の追加学習画像の描画濃度は0.004')
s=s.replace('v11_color/ALL_TRIALS_REBUILD03.md)','v11_color/ALL_TRIALS_REBUILD03.md)')
s=s.replace("    a,b=ps('v1.0'),ps('v1.1')", "    def refstat(g='all',k=None):return next(x for x in r['reference_statistics'] if x['group']==g and x['key']==k)\n    a,b=ps('v1.0'),ps('v1.1')")
s=s.replace("| {name} | {count(stat('v1.0',g,k))} | {count(stat('v1.1',g,k))} |", "| {name} | {count(stat('v1.0',g,k))} | {count(refstat(g,k))} | {count(stat('v1.1',g,k))} |")
s=s.replace('| 条件 | v1.0 | v1.1 |\n| --- | --- | --- |','| 条件 | v1.0：共通変換 | v1.0：教師定義に対応 | v1.1 |\n| --- | --- | --- | --- |')
s=s.replace("学習に使っていない4配置・2色・2開始条件で、v1.0は{count(stat('v1.0'))}、v1.1は{count(stat('v1.1'))}件成功しました。", "学習に使っていない4配置・2色・2開始条件で、v1.1は{count(stat('v1.1'))}件成功しました。v1.0は共通の変換で{count(stat('v1.0'))}、旧版の教師定義に合わせた変換で{count(refstat())}件でした。")
s=s.replace('同じ条件を対にすると、両モデル成功は', '最初の共通変換の比較を対にすると、両モデル成功は')
s=s.replace('表は固定試験で失敗した全件です。', '表は最初の固定42件で失敗した全件です。旧版の教師対応の16件は次節に全件を示します。')
point=s.index('    t5=')
extra='''    reference_rows=[]
    for row in r['reference_cases']:
        reference_rows.append(f"| {row['case']['id']} | {'成功' if row['success'] else '失敗'} | {row['hold_s']:.2f}秒 | [採点](v11_color/{row['score_path']}) / [入力・動作](v11_color/{row['record']}/record) |")
'''
s=s[:point]+extra+s[point:]
point=s.index('## 本当に画像と言葉で相手を選ぶか')
extra='''## 旧版と新版の動作定義の違いも確認する

旧版の教師は「距離誤差×0.7」の速度、新版は「距離誤差×1.4−機体速度×0.5」の速度を生成していました。最初の42件は新版向けの共通変換を使っているため、旧版の出力の意味に完全に一致する比較ではありません。この成績差を追加学習だけの効果とはしません。

そこで最初の42件を変更せず、旧版の教師コードの係数と速度更新の定義を復元した変換でも、同じ16条件を一度ずつ確認しました。VLAの重み、英語の指示、推論5回、追従制御の係数、開始状態と乱数、物理的な成功基準は同じです。変換式は旧版の教師ソースから決め、追加比較の結果を見て調整していません。v1.0の本来の動画用実行系そのものを再現する比較ではありません。

[実行前の登録](v11_color/protocol/rebuild03_v10_reference.json) / [旧版の教師](outputs/vla_data_realism_precision_02/teacher_source.py) / [変換式の代数確認](v11_color/reports/rebuild03_v10_decoder_preflight.json) / [全16件の再採点](v11_color/reports/rebuild03_v10_reference_verified.json)

| 条件 | v1.0・教師対応変換 | 目標範囲内の停止 | 記録 |
| --- | --- | --- | --- |
{chr(10).join(reference_rows)}

両方の旧版比較を残し、有利な方だけを選んでいません。画像と指示による対象選択は、次の**変換処理を通さないVLA出力の検査**でも確認します。

'''
s=s[:point]+extra+s[point:]
s=s.replace('## v1.1の検証', '[説明PDF（4ページ）](docs/説明資料_v1.1.pdf) / [全試験の記録](v11_color/ALL_TRIALS_REBUILD03.md)\n\n## v1.1の検証', 1)
s=s.replace('両方の旧版比較を残し、有利な方だけを選んでいません。', '[この16件の失敗した工程と入力画像](v11_color/reports/rebuild03_v10_reference_failure_details.json)も保存しています。両方の旧版比較を残し、有利な方だけを選んでいません。')
s=s.replace('python v11_color/scripts/verify_probe_rebuild03.py --no-write', 'python v11_color/scripts/verify_probe_rebuild03.py --no-write\npython v11_color/scripts/verify_v10_teacher_reference.py --no-write')
s=s.replace('誤認や誤接近を必ず防ぐ保証ではありません。', '対象を見失った場合は、任務管理が再捕捉や着陸へ切り替えます。')
s=s.replace('結果に応じた追加試行や係数変更は行っていません。', 'この固定42件では、失敗しても同じ条件の再実行や係数調整は行っていません。教師の定義と言語の違いを調べる参考比較は、別の計画として事前に記録し、全件を追加掲載しています。')
s=s.replace('保存記録の独立再採点', '保存ログからの再採点').replace('保存記録から独立に検算しました', '保存記録から再計算しました')
s=s.replace('32画像について、同じ画像・機体状態のまま指示を青／赤へ替えました。', '32画像について、同じ画像・機体状態のまま指示を青／赤へ替えました。推論は評価モードとし、動作生成の初期ノイズも同じ値を使っています（[実装](v11_color/runtime_rebuild03/smolvla_policy.py#L38)）。')
s=s.replace('動画の9場面と、v1.0が失敗した既知の配置1件を同じ最終モデルで確認しました。', '動画の9場面と、v1.0が失敗した既知の配置1件を、同じ最終モデルで各1回確認しました。')
s=s.replace("    t5=read(", "    language=read(W/'probe_v10_language/outputs/summary.json')['summary'][0]\n    assert read(W/'reports/v10_language_reference_verified.json')['all_consistent']\n    t5=read(")
s=s.replace('動画モデルの既存検査では、', '''旧版に不慣れな英語だけを使った影響も確認するため、同じ32画像・機体状態を旧版本来の英日併記の指示でも推論しました。結果は{language['correct_goal']}/64、4通りすべて正解{language['whole_quartet_correct']}/16組、角度差中央値{language['median_goal_angle_deg']:.1f}度でした。英語の結果もそのまま残しています。これは静止画像の追加確認であり、飛行比較の指示条件を変更したものではありません。[事前条件](v11_color/protocol/v10_language_reference.json) / [全出力](v11_color/probe_v10_language/outputs/raw_outputs.jsonl) / [再計算](v11_color/reports/v10_language_reference_verified.json)

動画モデルの既存検査では、''')
s=s.replace('python v11_color/scripts/verify_v10_teacher_reference.py --no-write', 'python v11_color/scripts/verify_v10_teacher_reference.py --no-write\npython v11_color/scripts/verify_v10_language_reference.py --no-write')
(W/'scripts/prepare_readme_rebuild03.py').write_text(s,encoding='utf-8')
