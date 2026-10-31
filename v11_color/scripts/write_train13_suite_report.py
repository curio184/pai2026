"""Write a dated full-suite report from completed, independently verified evidence."""
import datetime,json
from pathlib import Path
from run_round02_english import stress_pass
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
    suite='stress_train13_en';s=read(W/'runs'/suite/'summary.json');assert s['completed']==s['planned']==16
    diag=read(W/'reports'/(suite+'_phase_diagnostic.json'))
    geo=read(W/'reports'/(suite+'_perception_diagnostic.json'))
    power=read(W/'reports'/(suite+'_power_diagnostic.json'))
    corrected=read(W/'reports'/(suite+'_postflight_development_diagnostic_v2.json'))
    verification=read(W/'reports/train13_en_all_records_verified.json');assert verification['evidence_consistent']
    assert all(x['completed']==16 for x in [diag,geo,power,corrected])
    development=read(W/'runs/dev_train13_en/summary.json')
    result=read(W/'models/train13_en/result.json')
    components=diag['component_counts']['v1.1'];today=datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    lines=[f'追加検証・候補 train13 の全件報告（{today}）','',
      f'基本試験：{development["successes"]}/{development["planned"]} 成功。',
      f'配置試験：{s["successes"]}/16 成功。事前に定めた合格条件：{"達成" if stress_pass(s) else "未達"}。',
      f'指定人物への接近・停止が3秒以上：{components["requested_goal_hold_at_least_3s"]}/16。',
      f'離陸後の初期静止が3秒以上：{components["initial_hover_at_least_3s"]}/16。',
      '部分動作の成功数は原因を調べるための内訳であり、任務全体の成功率を置き換えません。',
      'これは学習設計の検討に使用済みの配置での開発試験です。未知配置での最終評価の証拠とは扱いません。','',
      '全16件（停止時間は従来の物理採点、距離は飛行中の人物との最小水平距離）',
      'ID / 配置 / 色 / 全体 / 目標停止[秒] / 初期静止[秒] / 最小距離[m] / 不合格項目']
    for r in diag['cases']:
        c=r['case'];failed=r['failed_checks']+r['failed_physical_components']
        lines.append(f'{c["id"]} / {c["scene"]} / {c["color"]} / {"成功" if r["success"] else "不成功"} / {r["approach_hold_s"]:.3f} / {r["explicit_hover_hold_s"]:.3f} / {r["minimum_person_clearance_m"]:.3f} / {", ".join(failed) if failed else "なし"}')
    lines.extend(['','学習と記録',f'最終ステップ：{result["optimizer_steps_completed"]}。途中の重みを成績で選んでいません。',
      f'最終モデル SHA-256：{result["checkpoint_sha256"]}',
      '元のモデル・動画・PDFと、今回の成功・失敗の全記録を保存しています。',
      'WSLは4CPU・8GiBを上限とし、飛行は1件ずつ実行しています。',
      '事後分析用の教師参照に誤りがあったため、teacher13を参照するv2の分析結果を使用しています。元の分析も保存し、訂正理由を記録しています。採点や飛行記録に変更はありません。','',
      '根拠ファイル',str(W/'runs'/suite/'suite_plan.json'),str(W/'runs'/suite/'summary.json'),
      str(W/'reports'/(suite+'_phase_diagnostic.json')),str(W/'reports'/(suite+'_perception_diagnostic.json')),
      str(W/'reports'/(suite+'_power_diagnostic.json')),str(W/'reports'/(suite+'_postflight_development_diagnostic_v2.json')),
      str(W/'reports/train13_en_all_records_verified.json'),str(W/'reports/train13_diagnostic_reference_correction.json'),'',
      '未完了',
      '任務全体の安定性の改善、既存動画の全場面の回帰試験、未使用配置でのv1.0/v1.1比較、未使用画像での指示・色の入れ替え検査。',
      '上記の証拠に基づく4ページPDFとREADMEの完成・点検。push・タグ付け・再提出は未実施で、承認が必要です。'])
    dest=W/'reports/train13_completed_suite_report.txt';assert not dest.exists();dest.write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps(dict(report=str(dest),successes=s['successes'],gate=stress_pass(s)),ensure_ascii=False))
if __name__=='__main__':main()
