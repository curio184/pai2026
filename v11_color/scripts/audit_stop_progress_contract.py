"""Postflight description of all 16 saved cases, never a replacement score.

Uses ground truth only to describe already recorded physically valid intervals.
Does not replay a changed controller or claim any counterfactual success.
"""
from pathlib import Path
import datetime
import hashlib
import json
import numpy as np

W = Path(__file__).resolve().parents[1]

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def longest(t, mask):
    start = None
    best = 0.0
    for time, valid in zip(t, mask):
        if valid:
            if start is None:
                start = float(time)
            best = max(best, float(time) - start)
        else:
            start = None
    return best

def pct(values):
    return np.percentile(values, [0, 50, 95, 100]).tolist() if len(values) else None

def main():
    cases = []
    summary_path = W/'runs/stress_train15_en/summary.json'
    for case in read(summary_path)['cases']:
        p = Path(case['record'])
        score = read(p/'physical_score.json')
        color = score['profile']
        records = [json.loads(line) for line in (p/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
        traces = [r for r in records if r['phase'] == color and r['estimated_state'] is not None]
        out = dict(id=case['id'], original_success=case['success'], record=str(p),
                   trace_sha256=sha(p/'trace.jsonl'), score_sha256=sha(p/'physical_score.json'),
                   samples=len(traces), saved_goal_hold_s=score['goal_holds'][color]['physical_hold']['duration_s'])
        if traces:
            t = np.array([r['t'] for r in traces])
            truth = np.array([r['truth'] for r in traces])
            own = np.array([r['estimated_state'] for r in traces])
            action = np.array([r['model_action'] for r in traces])
            is_policy = np.array([r['action_source']=='policy' for r in traces])
            goal = np.array(score['goal_holds'][color]['goal_scene_xy_m'])
            physical_speed = np.linalg.norm(truth[:,4:6], axis=1)
            estimated_speed = np.linalg.norm(own[:,:2], axis=1)
            distance = np.linalg.norm(truth[:,[2,1]] - goal, axis=1)
            valid = (distance<=.25)&(physical_speed<=.08)&(-truth[:,3]>=.8)&(-truth[:,3]<=1.25)
            # No merging across re-acquisition gaps: add the missing samples back
            # as invalid before measuring any continuous interval.
            full_mask = []
            for r in records:
                s = r.get('estimated_state')
                full_mask.append(r['phase']==color and s is not None and np.linalg.norm(s[:2])<.08 and r['action_source']=='policy')
            out.update(
                physically_valid_samples=int(valid.sum()),
                estimated_speed_during_physically_valid_p0_p50_p95_p100=pct(estimated_speed[valid]),
                command_norm_during_physically_valid_p0_p50_p95_p100=pct(np.linalg.norm(action[valid,:2],axis=1)),
                estimated_speed_fails_during_physically_valid=int((estimated_speed[valid]>=.08).sum()),
                not_policy_during_physically_valid=int((~is_policy[valid]).sum()),
                longest_estimated_low_speed_and_policy_s=longest([r['t'] for r in records], full_mask),
                non_policy_sources_during_physically_valid={s:sum(1 for r,v in zip(traces,valid) if v and r['action_source']==s)
                                                           for s in sorted({r['action_source'] for r,v in zip(traces,valid) if v and r['action_source']!='policy'})},
                limits='Sampled trace; describes conditions only. The complete runtime additionally uses stage age, a time-weighted command window and three-image confirmation. No exact transition replay is asserted.')
        cases.append(out)
    h09=next(c for c in cases if c['id']=='H09')
    assert h09['estimated_speed_fails_during_physically_valid']==0
    report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                source_summary_sha256=sha(summary_path), cases=cases,
                finding='H09の物理的に有効な停止区間では、推定水平速度も全サンプルで0.08m/s未満。待ち時間を推定速度の超過だけで説明することはできない。policy以外への切替と指令窓・画像確認を切り分ける必要がある。',
                no_new_flight=True, no_model_inference=True, no_training=True,
                no_scoring_changes=True, no_counterfactual_success_claim=True)
    p=W/'reports/stop_progress_contract_audit_train15.json'
    with p.open('x', encoding='utf-8') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
        f.write('\n')
    print(json.dumps(dict(output=str(p),sha256=sha(p),cases=len(cases),H09=h09),ensure_ascii=False))

if __name__=='__main__':
    main()
