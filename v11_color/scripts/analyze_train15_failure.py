"""Join the complete, independently rescored candidate15 development evidence."""
import datetime
import hashlib
import json
from pathlib import Path
from run_round02_english import stress_pass

W = Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    suite = 'stress_train15_en'
    s = read(W/'runs'/suite/'summary.json')
    assert s['completed'] == s['planned'] == 16
    names = {
        'phase': suite+'_phase_diagnostic.json',
        'teacher': suite+'_postflight_development_diagnostic.json',
        'geometry': suite+'_perception_diagnostic.json',
        'power': suite+'_power_diagnostic.json',
        'stationary': suite+'_stationary_full_v2.json',
        'independent_rescore': 'train15_en_all_records_verified.json',
        'linear_diagnostic01': 'stationary_feedback_analysis01.json',
        'linear_diagnostic02': 'stationary_feedback_analysis02.json',
        'input_coverage': 'train15_attitude_teacher_input_coverage.json',
    }
    source = {k: read(W/'reports'/v) for k,v in names.items()}
    assert source['independent_rescore']['evidence_consistent']
    for k in ['phase','teacher','geometry','power','stationary']:
        assert source[k]['completed'] == 16
    teacher = {r['id']:r for r in source['teacher']['cases']}
    stationary = {r['id']:r for r in source['stationary']['cases']}
    rows = []
    for r in source['phase']['cases']:
        cid = r['case']['id']
        td = teacher[cid]
        row = {k:r[k] for k in ['case','success','mission_failure','approach_hold_s',
               'minimum_goal_distance_m','explicit_hover_hold_s','minimum_person_clearance_m',
               'failed_checks','failed_physical_components']}
        row['executed_imitation_by_phase'] = {
            phase:p.get('actual_execution') for phase,p in td['phases'].items()}
        row['stationary_diagnostic'] = stationary[cid].get('initial_hover_before_first_power_event')
        row['power_events'] = stationary[cid]['power_events']
        row['record'] = str(W/'runs'/suite/(cid+'_v1.1')/'record')
        rows.append(row)
    result = read(W/'models/train15_en/result.json')
    report = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        candidate='train15_en', final_checkpoint_sha256=result['checkpoint_sha256'],
        development=read(W/'runs/dev_train15_en/summary.json')['successes'],
        development_planned=8, stress_successes=s['successes'], stress_planned=16,
        stress_gate_met=stress_pass(s), components=source['phase']['component_counts'],
        cases=rows, sources={k:dict(path=str(W/'reports'/v),sha256=sha(W/'reports'/v))
                           for k,v in names.items()},
        findings=[
          'Basic development suite passed 8/8; the separately registered stress suite determines whether the candidate proceeds. Neither is untouched final evaluation.',
          'In H06, a persistent estimated-roll offset accompanies continued horizontal drift. Battery failsafe, thrust-loss and crash/disarm statuses occur later. This does not isolate a unique physical cause.',
          'H08 reported a visible red person but never reached the required goal region; its notification image is not evidence of successful physical approach.',
          'Low saved teacher-imitation error in stationary phases does not demonstrate that the teacher stabilizes the delayed physical system.',
          'Linear diagnostics suggest an attitude-assisted, leaky teacher request may reduce sustained disturbance while avoiding some delayed-feedback oscillation. This is a hypothesis, not verified flight improvement.'
        ],
        next_hypothesis='Consider relabeling only stationary horizontal training targets using existing estimated velocity and attitude, leaving all runtime code, navigation targets, input arrays and success conditions unchanged. A separate preregistration and final-step training are required before proceeding.',
        scope='All sixteen exposed development runs, including failures; original records and model preserved. No score change, policy call, retry or held-out evaluation performed by this report.',
        limitations='The linear diagnostic has no camera, VLA, EKF, noise, rotation, vertical flight or battery. Its 324/432 analytical parameter cases are not additional flight trials and must never be pooled with flight success rates.')
    dest = W/'reports/train15_failure_analysis.json'
    text_dest = W/'reports/train15_completed_suite_report.txt'
    assert not dest.exists() and not text_dest.exists()
    dest.write_text(json.dumps(report,indent=2),encoding='utf8')
    lines = ['候補 train15 の検証結果', '',
             '基本試験：8回中8回成功。',
             f'配置・開始条件を変えた試験：16回中{s["successes"]}回成功。',
             '以下は全件です。失敗を除外していません。開発に使用済みの条件であり、最終評価ではありません。', '',
             'ID / 色 / 全体 / 対象前での停止 [秒] / 初期静止 [秒] / 最小対人距離 [m] / 不合格項目']
    for r in rows:
        failed = r['failed_checks'] + r['failed_physical_components']
        lines.append(f'{r["case"]["id"]} / {r["case"]["color"]} / {"成功" if r["success"] else "失敗"} / '
                     f'{r["approach_hold_s"]:.3f} / {r["explicit_hover_hold_s"]:.3f} / '
                     f'{r["minimum_person_clearance_m"]:.3f} / {", ".join(failed) if failed else "なし"}')
    lines.extend(['', '分析',
        'H06では、姿勢推定のずれと横流れが継続し、後から電池低下・推力不足・クラッシュによる停止が記録されています。原因を一つに断定するものではありません。',
        'H08では赤い服の人物を確認して画像を保存しましたが、指定の目標点から25cm以内には到達していません。画像の保存だけでは成功としません。',
        '姿勢情報を使う教師動作は、数式モデルで検討した段階です。実際の飛行で改善したという証拠にはなりません。', '',
        '未完了：安定性の改善、未使用配置での比較、動画の全場面の回帰確認、最終PDFとREADME。',
        '動画・v1.0の重み・過去の記録は保持。push・タグ付け・再提出は未実施です。', '',
        '根拠：'+str(dest), '最終モデル SHA-256：'+result['checkpoint_sha256']])
    text_dest.write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps(dict(report=str(dest),text_report=str(text_dest),successes=s['successes'],gate=stress_pass(s),sha256=sha(dest))))

if __name__ == '__main__': main()
