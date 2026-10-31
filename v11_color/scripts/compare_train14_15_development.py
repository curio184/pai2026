"""Compare every saved development case; no new inference or altered scoring."""
import datetime,hashlib,json
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
dest=W/'reports/train15_development_comparison.json';assert not dest.exists()
summaries={c:read(W/'runs'/('dev_'+c)/'summary.json') for c in ['train14_en','train15_en']}
assert all(s['completed']==s['planned']==8 for s in summaries.values())
assert [r['case'] for r in summaries['train14_en']['cases']]==[r['case'] for r in summaries['train15_en']['cases']]
rows=[]
for index in range(8):
    case=summaries['train14_en']['cases'][index]['case'];row=dict(case=case,models={})
    for candidate,summary in summaries.items():
        outcome=summary['cases'][index];rec=W/'runs'/('dev_'+candidate)/(case['id']+'_'+case['model'])/'record'
        score=read(rec/'physical_score.json');color=case.get('color',case.get('profile'))
        trace=[json.loads(x) for x in (rec/'trace.jsonl').read_text().splitlines()]
        rotations={}
        for phase in ['right','left']:
            part=[r for r in trace if r['phase']==phase]
            if not part:continue
            final=[r for r in part if r['t']>=part[-1]['t']-2];truth=np.array([r['truth'] for r in final])
            rotations[phase]=dict(**score['rotations'][phase],
                final2s_horizontal_speed_max_m_s=float(np.linalg.norm(truth[:,4:6],axis=1).max()),
                final2s_yaw_rate_abs_max_rad_s=float(np.abs(truth[:,31]).max()))
        row['models'][candidate]=dict(success=outcome['success'],
            requested_goal_hold_s=score['goal_holds'][color]['physical_hold']['duration_s'] if color in ['blue','red'] else None,
            initial_hover_s=score['explicit_hover_instruction_hold']['duration_s'],
            minimum_person_clearance_m=score['minimum_person_clearance_m'],rotations=rotations,
            record=str(rec),trace_sha256=sha(rec/'trace.jsonl'),physical_score_sha256=sha(rec/'physical_score.json'),
            checkpoint_sha256=outcome['checkpoint_sha256'])
    rows.append(row)
report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope='All8 previously exposed development cases, compared postflight. Not an unseen-layout test, repeated-trial success-rate estimate, or new flight.',
    candidate_successes={c:s['successes'] for c,s in summaries.items()},cases=rows,
    changed_training='Stationary teacher braking1.6->0.6; all input arrays and all navigation/landing/nonhorizontal targets preserved.6000 additional steps,new training seed.',
    causal_limit='The changes in training targets, further optimization and random seed are not isolated. Saved waveforms support a delayed-feedback hypothesis, not a unique causal proof.',
    scorer_and_runtime_unchanged=True,source_script_sha256=sha(Path(__file__)))
dest.write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(dict(report=str(dest),sha256=sha(dest),successes=report['candidate_successes'],
    previous_failures=[dict(id=r['case']['id'],old=r['models']['train14_en']['rotations'],new=r['models']['train15_en']['rotations']) for r in rows if not r['models']['train14_en']['success']])))
