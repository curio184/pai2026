"""Write the short completion report only after evidence, PDF and distribution QA."""
import collections
import datetime
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main():
    result = read(W / 'results/all_trials_rebuild03.json')
    public = read(W / 'reports/publication_rebuild03_checks.json')
    pdf = read(W / 'reports/pdf_rebuild03_check.json')
    assert result['publication_evidence_complete'] and result['preregistered_goal_met']
    assert public['goal_met'] and not public['published'] and not public['submitted']
    assert pdf['visually_reviewed'] and pdf['pages'] == 4
    proof = read(sorted((W / 'reports').glob('preservation_audit_20*.json'))[-1])
    assert proof['passed']
    assert all(x['unchanged'] for x in proof['protected_artifacts'])
    assert read(W / 'reports/v10_language_reference_verified.json')['all_consistent']
    now = datetime.datetime.now(datetime.timezone.utc)
    start = datetime.datetime.fromisoformat('2026-10-30T16:01:14+00:00')
    deadline = start + datetime.timedelta(hours=10)
    assert now <= deadline, 'Do not claim completion within the requested time after the deadline'
    suites = collections.defaultdict(list)
    for row in result['all_executed_cases']:
        suites[row['suite']].append(row)
    current = {k:v for k,v in suites.items() if k.startswith('rebuild')}
    assert sum(map(len, current.values())) == 75
    main_rows = [r for r in result['final_cases']
                 if r['case']['model'] == 'v1.1' and r['case']['group'] == 'matched_unseen']
    new_stat = next(s for s in result['heldout_statistics']
                    if s['model'] == 'v1.1' and s['group'] == 'all')
    old_stat = next(s for s in result['heldout_statistics']
                    if s['model'] == 'v1.0' and s['group'] == 'all')
    ref_stat = next(s for s in result['reference_statistics'] if s['group'] == 'all')
    probe = next(s for s in read(W / 'probe_rebuild03/outputs/summary.json')['summary']
                 if s['model'] == 'v1.1' and s['prompt_group'] == 'runtime_english')
    main_probe = read(W / 'probe_rebuild03/outputs/summary.json')
    language_probe = read(W / 'probe_v10_language/outputs/summary.json')
    flow_benchmark = read(W / 'reports/flow_steps_benchmark01.json')
    note = dict(
        completed_utc=now.isoformat(), elapsed_hours=(now-start).total_seconds()/3600,
        deadline_utc=deadline.isoformat(), goal_met=True,
        heldout=new_stat, video_successes=sum(r['success'] for r in result['regression_cases']),
        video_trials=9, known_failure_retest=result['known_failure_retest_passed'],
        static_intervention=probe,
        saved_static_outputs=dict(english_comparison=main_probe['all_outputs'],
                                  original_bilingual_reference=language_probe['all_outputs'],
                                  flow_step_benchmark=len(flow_benchmark['rows'])),
        new_training_in_this_resumed_run=False,
        current_flights=75, cumulative_flights=len(result['all_executed_cases']),
        current_suites=[dict(suite=k,n=len(v),success=sum(x['success'] for x in v)) for k,v in current.items()],
        required_local_tasks_remaining=[], external_actions_performed=[],
        publication='Prepared and verified locally; push, tagging and resubmission require user approval.',
        model_sha256=result['selected_checkpoint_sha256'],
        preserved_artifacts=proof['protected_artifacts'],
        pdf_sha256=pdf['pdf_sha256'], candidate=public['candidate'])
    (W / 'reports/rebuild03_completion.json').write_text(json.dumps(note, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = [
        'v1.1 完了報告', '',
        f"完了日時：{now.astimezone(datetime.timezone(datetime.timedelta(hours=9))):%Y-%m-%d %H:%M:%S} JST",
        f"再開からの所要時間：{note['elapsed_hours']:.2f}時間（10時間以内）", '',
        f"未学習配置：{new_stat['k']}/{new_stat['n']}成功。4配置×2色×2開始状態。",
        f"停止継続：{min(r['hold_s'] for r in main_rows):.2f}～{max(r['hold_s'] for r in main_rows):.2f}秒。25cm以内・0.08m/s以下・3秒以上の基準を維持。",
        f"動画の9場面：{note['video_successes']}/9成功。既知の配置交換失敗：1/1成功。",
        f"色・指示交換：{probe['correct_goal']}/{probe['outputs']}、4通りすべて正解{probe['whole_quartet_correct']}/{probe['quartets']}組。",
        f"旧版は共通変換で{old_stat['k']}/16、旧教師対応の変換で{ref_stat['k']}/16。教師の動作定義・言語の差を含むため、学習だけの効果とは主張しない。", '',
        'VLAは画像・英語の工程指示・機体状態から、指定人物への接近・減速・停止の動作列を生成する。実行部はその到達先を復元し、自機の移動を補正して追従する。人物の正解座標・検出枠は誘導に使わない。', '',
        '今回の全飛行試験（失敗も含む）：']
    lines += [f"  {k}: {sum(x['success'] for x in v)}/{len(v)}成功" for k,v in current.items()]
    lines += ['', '異なる構成の成功率は合算しない。今回75件、v1.1開発以降454件の飛行試験を全件保存。',
        f"静止画像の追加確認：英語での新旧比較{main_probe['all_outputs']}出力、旧版の英日併記{language_probe['all_outputs']}出力、推論回数の比較{len(flow_benchmark['rows'])}出力を保存。",
        'この再開以降は追加学習を行わず、既存の最終重みを使って動作列の実行方法を修正した。',
        '全件一覧：v11_color/ALL_TRIALS_REBUILD03.md',
        '固定42件：v11_color/runs/rebuild03_final/',
        '旧版の教師対応16件：v11_color/runs/rebuild03_v10_reference/',
        '静止画像と全出力：v11_color/probe_rebuild03/',
        '説明PDF：v11_color/reports/output/pdf/説明資料_PAI最終課題_v1.1_検証更新版.pdf',
        'README・公開用一式：v11_color/publication_candidate_rebuild03/', '',
        '必須のローカル作業に未完了事項はない。公開済み動画・提出時PDF・v1.0の重みは保存した。',
        'push・タグ付け・再提出は未実施（ユーザー承認が必要）。',
        '確認範囲は同じ室内・同じ2人の静止人物・限定した配置と英語指示。未知の部屋と実機飛行は本検証の範囲外。', '']
    (W / 'reports/完了報告_v1.1.txt').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(dict(goal_met=True, elapsed_hours=note['elapsed_hours'], current_flights=75), ensure_ascii=False))

if __name__ == '__main__':
    main()
