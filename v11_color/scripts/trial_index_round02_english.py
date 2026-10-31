"""Full trial index with candidate identity, prompt language and failure metrics."""
import json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
r=read(W/'results/all_trials_round02_english.json')
identities={read(p)['checkpoint_sha256']:p.parent.name for p in (W/'models').glob('*/result.json')}
lines=['# 追加検証の全実行','',
    '失敗した最初の最終評価、開発確認、英語へ統一した次の最終評価を分けて記載しています。成功例だけの一覧ではありません。動画はv1.0のままです。',
    '', '| 区分 | 試験 | 重み | 指示 | 結果 | 停止時間 | 目標点への最短距離 | 人物への最小距離 | 記録 |',
    '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
for row in r['all_executed_cases']:
    case=row['case'];folder=W/row['record'];manifest=read(folder/'manifest.json')
    language='英語' if manifest.get('prompt_language')=='English' else '英日併記'
    identity='v1.0' if case['model']=='v1.0' else identities.get(row.get('checkpoint_sha256'),'不明：記録を参照')
    result='成功' if row['success'] else ('実行基盤のエラー' if row.get('error') else '失敗')
    hold=f"{row['hold_s']:.3f}秒" if row.get('hold_s') is not None else '-'
    distance=f"{row['min_goal_distance_m']:.3f}m" if row.get('min_goal_distance_m') is not None else '-'
    clearance=f"{row['min_person_clearance_m']:.3f}m" if row.get('min_person_clearance_m') is not None else '-'
    link=row.get('score_path',row['record']+'/outcome.json')
    lines.append(f"| {row['suite']} | {case['id']} | {identity} | {language} | {result} | {hold} | {distance} | {clearance} | [採点・記録]({link}) |")
lines+=['',f"実行済み：{len(r['all_executed_cases'])}件。条件付きで未実行：{len(r['not_executed_cases'])}件。未実行を失敗には数えません。",'']
for row in r['not_executed_cases']:lines.append(f"- {row['suite']} / {row['case']['id']} / {row['case']['model']}")
lines+=['','停止時間は接近期に採点条件を連続して満たした最長時間です。目標点への距離は、対象者の前0.9mの採点点への距離です。人物への最小距離は、飛行中にいずれかの人物へ近づいた最短の水平距離で、目標点への距離とは区別しています。',
    '入力画像・生成した動作・機体状態・任務の工程・事後採点は、各試験フォルダーに保存しています。',
    '', '最初の最終評価：`runs/heldout_train03`。その結果を用いた改善後の最終評価：`runs/heldout_round02_english_*`。両者を合算した成功率は報告しません。',
    '英語の指示への変更は、次の学習と最終評価を始める前に登録しました。以前の英日併記の記録はそのまま残しています。','']
out=W/'ALL_TRIALS_ROUND02_ENGLISH.md';out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(out)
