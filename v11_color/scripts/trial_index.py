import json
from pathlib import Path
W=Path(__file__).resolve().parents[1];r=json.loads((W/'results/all_trials.json').read_text(encoding='utf-8'))
lines=['# 追加検証の全実行','','開発確認と最終評価を分け、失敗も含めて記載しています。動画はv1.0のままです。未実行は失敗として扱わず、別に記載します。','','| 区分 | 試験 | モデル | 結果 | 停止時間 | 目標点への最短距離 | 記録 |','| --- | --- | --- | --- | --- | --- | --- |']
for row in r['all_executed_cases']:
    case=row['case'];hold=f"{row['hold_s']:.3f}秒" if row.get('hold_s') is not None else '-';dist=f"{row['min_goal_distance_m']:.3f}m" if row.get('min_goal_distance_m') is not None else '-'
    link=row.get('score_path',row['record']+'/outcome.json')
    result='成功' if row['success'] else ('実行基盤のエラー' if row.get('error') else '失敗')
    lines.append(f"| {row['suite']} | {case['id']} | {case['model']} | {result} | {hold} | {dist} | [採点・記録]({link}) |")
lines+=['','未実行：'+str(len(r['not_executed_cases']))+'件。','']
for row in r['not_executed_cases']:lines.append(f"- {row['suite']} / {row['case']['id']} / {row['case']['model']}")
lines+=['','停止時間と最短距離は、対象者の前に設定した目標点に対する値です。人物そのものへの距離ではありません。','詳細な条件、全画像、生成した動作、事後採点は各試験フォルダーにあります。']
(W/'ALL_TRIALS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
