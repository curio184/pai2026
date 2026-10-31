"""Report every planned flight, including failures and not-yet-run cases."""
import json,math,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wilson(k,n):
    if not n:return None
    z=1.959963984540054;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;r=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [c-r,c+r]
plan=read(W/'protocol/plan.json');allrows=[];notrun=[]
for suite in sorted((W/'runs').glob('*')):
    if not (suite/'suite_plan.json').exists():continue
    sp=read(suite/'suite_plan.json')
    for case in sp['cases']:
        folder=suite/(case['id']+'_'+case['model']);row=dict(suite=suite.name,case=case,record=folder.relative_to(W).as_posix())
        if not (folder/'outcome.json').exists():notrun.append(row);continue
        outcome=read(folder/'outcome.json');row.update(success=outcome['success'],error=outcome.get('error'),flight_started=outcome['flight_started'])
        scorefile=folder/'record'/('search_score.json' if case['kind']=='search' else 'physical_score.json')
        if scorefile.exists():
            score=read(scorefile);physical=score['physical'] if case['kind']=='search' else score
            target=case.get('color',case.get('profile'))
            if target in ['blue','red']:
                goal=physical['goal_holds'][target];row['hold_s']=goal['physical_hold']['duration_s'];row['min_goal_distance_m']=goal['minimum_goal_distance_m']
                row['other_min_goal_distance_m']=physical['goal_holds']['red' if target=='blue' else 'blue']['minimum_goal_distance_m']
            row.update(min_person_clearance_m=physical.get('minimum_person_clearance_m'),score_path=scorefile.relative_to(W).as_posix(),score_sha256=sha(scorefile))
        resultfile=folder/'record/result.json'
        if resultfile.exists():
            result=read(resultfile);row.update(stop_reason=result['stop_reason'],mission_failure=result.get('mission_failure'))
        allrows.append(row)
heldout=[r for r in allrows if r['suite'].startswith('heldout')];stats=[]
for version in ['v1.0','v1.1']:
    for group,key in [('all',None),('color','blue'),('color','red')]+[('layout',l['name']) for l in plan['heldout_layouts']]:
        rr=[r for r in heldout if r['case']['model']==version and (group=='all' or r['case']['color' if group=='color' else 'scene']==key)]
        k=sum(r['success'] for r in rr);n=len(rr)
        stats.append(dict(model=version,group=group,key=key,k=k,n=n,wilson95=wilson(k,n)))
candidate=read(W/'protocol/selected_final.json')['candidate'] if (W/'protocol/selected_final.json').exists() else None
if candidate is None:
    # Suite folders are created only when execution is allowed. Their absence
    # must not make the remaining preregistered final evaluation disappear.
    for case in plan['heldout_cases']:
        for version in ['v1.0','v1.1']:
            notrun.append(dict(suite='heldout_final_candidate_pending',case=dict(**case,kind='search',model=version),reason='Final candidate has not passed the development and regression gates'))
    for scene,color in [('clear','blue'),('clear','red'),('fog_light','blue'),('fog_dense','blue'),('dust','blue')]:
        notrun.append(dict(suite='regression_final_candidate_pending',case=dict(id=scene+'_'+color,scene=scene,color=color,kind='search',model='v1.1'),reason='Final candidate not selected'))
    notrun.append(dict(suite='known_failure_final_candidate_pending',case=dict(id='T3_blue_retest',scene='known_swapped',color='blue',kind='search',model='v1.1'),reason='Final candidate not selected'))
reg=[r for r in allrows if candidate and (r['suite']=='regression_'+candidate or r['suite']=='dev_'+candidate and r['case']['kind']=='primitive')]
v11=[s for s in stats if s['model']=='v1.1'];gate=False
if v11 and reg:
    gate=v11[0]['n']==16 and v11[0]['k']>=14 and all(s['k']>=7 for s in v11 if s['group']=='color') and all(s['k']>=3 for s in v11 if s['group']=='layout') and len(reg)==9 and all(r['success'] for r in reg)
closed_loop_gate=gate
probe_gate=False
if (W/'probe/outputs/summary.json').exists():
    pp=read(W/'probe/outputs/summary.json')
    ps=next(s for s in pp['summary'] if s['model']=='v1.1' and s['prompt_group']=='runtime_bilingual')
    probe_gate=ps['outputs']==64 and ps['correct_goal']>=60 and ps['quartets']==16 and ps['whole_quartet_correct']>=14
known=[r for r in allrows if candidate and r['suite']=='known_failure_'+candidate]
known_gate=len(known)==1 and known[0]['success']
gate=bool(closed_loop_gate and probe_gate and known_gate)
out=W/'results';out.mkdir(exist_ok=True)
report=dict(plan_sha256=sha(W/'protocol/plan.json'),completion_addendum_sha256=sha(W/'protocol/completion_addendum.json'),all_executed_cases=allrows,not_executed_cases=notrun,heldout_statistics=stats,regression_cases=reg,preregistered_goal_met=gate,closed_loop_gate_met=closed_loop_gate,color_intervention_gate_met=probe_gate,known_failure_retest_passed=bool(known_gate),known_failure_cases=known,
    limits=['One room, two static avatar identities; held-out layouts lie in the same constrained spatial range as training.','Small, correlated simulator sample; Wilson intervals describe these Bernoulli trials, not deployment reliability.','Runtime still uses original bilingual stage prompts. Detector and mission manager are not replaced by VLA.','No physical drone flight, arbitrary rooms, or unbounded layout claims.'],video_model='v1.0, unchanged')
(out/'all_trials.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(executed=len(allrows),not_executed=len(notrun),preregistered_goal_met=gate,statistics=stats),ensure_ascii=False),flush=True)
