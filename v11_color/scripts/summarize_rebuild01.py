"""Read-only aggregation of the one fixed confirmation; never changes acceptance."""
import argparse, hashlib, json, math
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def wilson(k,n):
    if not n:return None
    z=1.959963984540054;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;r=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [c-r,c+r]
def main():
    plan=read(W/'protocol/rebuild01_final.json');root=W/'runs/rebuild01_final'
    rows=[];pending=[]
    for case in plan['cases']:
        folder=root/(case['id']+'_'+case['model']);outcome=folder/'outcome.json'
        if not outcome.exists():pending.append(case);continue
        o=read(outcome);m=read(folder/'manifest.json')
        assert o['case']==case and m['case']==case
        assert m['checkpoint_sha256']==plan['checkpoint_sha256' if case['model']=='v1.1' else 'old_checkpoint_sha256']
        assert m['runtime_lock_sha256']==sha(W/'protocol/rebuild01_final.json')
        row=dict(suite='rebuild01_final',case=case,record=folder.relative_to(W).as_posix(),success=o['success'],
                 error=o.get('error'),flight_started=o['flight_started'],checkpoint_sha256=m['checkpoint_sha256'],
                 outcome_sha256=sha(outcome),manifest_sha256=sha(folder/'manifest.json'))
        f=folder/'record'/('search_score.json' if case['kind']=='search' else 'physical_score.json')
        if f.exists():
            s=read(f);p=s['physical'] if case['kind']=='search' else s;target=case.get('color',case.get('profile'))
            assert s['success']==o['success']
            row.update(score_path=f.relative_to(W).as_posix(),score_sha256=sha(f),checks=s.get('checks'),
                       min_person_clearance_m=p.get('minimum_person_clearance_m'),
                       hover_hold_s=p['explicit_hover_instruction_hold']['duration_s'])
            if target in ('blue','red'):
                g=p['goal_holds'][target]
                row.update(hold_s=g['physical_hold']['duration_s'],min_goal_distance_m=g['minimum_goal_distance_m'],
                           other_min_goal_distance_m=p['goal_holds']['red' if target=='blue' else 'blue']['minimum_goal_distance_m'])
        f=folder/'record/result.json'
        if f.exists():
            r=read(f);row.update(stop_reason=r['stop_reason'],mission_failure=r.get('mission_failure'))
        rows.append(row)
    held=[r for r in rows if r['case']['group']=='matched_unseen'];stats=[]
    paired=[]
    for cid in sorted({r['case']['id'] for r in held}):
        pair={r['case']['model']:r for r in held if r['case']['id']==cid}
        if set(pair)=={'v1.0','v1.1'}:
            paired.append(dict(case=cid,v10_success=pair['v1.0']['success'],v11_success=pair['v1.1']['success']))
    paired_counts={name:sum((r['v10_success'],r['v11_success'])==values for r in paired)
                   for name,values in [('both_success',(True,True)),('v11_only',(False,True)),('v10_only',(True,False)),('both_failure',(False,False))]}
    layouts=sorted({c['scene'] for c in plan['cases'] if c['group']=='matched_unseen'})
    for model in ('v1.0','v1.1'):
        for group,key in [('all',None),('color','blue'),('color','red')]+[('layout',n) for n in layouts]:
            rr=[r for r in held if r['case']['model']==model and (group=='all' or r['case']['color' if group=='color' else 'scene']==key)]
            n=len(rr);k=sum(r['success'] for r in rr);stats.append(dict(model=model,group=group,key=key,k=k,n=n,wilson95=wilson(k,n)))
    vv=[s for s in stats if s['model']=='v1.1']
    flight=bool(len(held)==32 and vv[0]['n']==16 and vv[0]['k']>=14
                and all(s['n']==8 and s['k']>=7 for s in vv if s['group']=='color')
                and all(s['n']==4 and s['k']>=3 for s in vv if s['group']=='layout'))
    reg=[r for r in rows if r['case']['group']=='video_regression']
    known=[r for r in rows if r['case']['group']=='known_failure']
    regression=len(reg)==9 and all(r['success'] for r in reg)
    known_ok=len(known)==1 and known[0]['success']
    probe=W/'probe_rebuild01/outputs/summary.json';probe_ok=False;probe_checked=False
    if probe.exists():
        q=next(s for s in read(probe)['summary'] if s['model']=='v1.1' and s['prompt_group']=='runtime_english')
        probe_ok=q['outputs']==64 and q['correct_goal']>=60 and q['quartets']==16 and q['whole_quartet_correct']>=14
        f=W/'reports/probe_rebuild01_verified.json'
        if f.exists():
            proof=read(f);probe_checked=proof['all_consistent'] and any(r['probe']=='rebuild01' and r['summary_sha256']==sha(probe) and r['raw_sha256']==sha(probe.parent/'raw_outputs.jsonl') for r in proof['probes'])
    f=W/'reports/rebuild01_final_execution_verified.json';verified=False;execution=False
    if f.exists():
        proof=read(f);verified=proof['all_verified'] and proof['records']==len(rows)==42
        execution=verified and all(r['decoder_and_tracking_algebra_verified'] for r in proof['cases'])
    original=read(W/'results/all_trials_receipt.json')
    history=list(original['all_executed_cases'])
    for suite in ['rebuild01_dev','rebuild01_expanded']:
        for op in sorted((W/'runs'/suite).glob('*/outcome.json')):
            o=read(op);m=read(op.parent/'manifest.json')
            sp=op.parent/'record'/('search_score.json' if o['case']['kind']=='search' else 'physical_score.json')
            history.append(dict(suite=suite,case=o['case'],record=op.parent.relative_to(W).as_posix(),
                success=o['success'],error=o.get('error'),flight_started=o['flight_started'],
                checkpoint_sha256=m['checkpoint_sha256'],outcome_sha256=sha(op),manifest_sha256=sha(op.parent/'manifest.json'),
                score_path=sp.relative_to(W).as_posix(),score_sha256=sha(sp)))
    assert len(history)==405 and len({r['record'] for r in history})==405
    gate=bool(flight and regression and known_ok and probe_ok and probe_checked and verified and execution and not pending)
    result=dict(candidate=plan['candidate'],configuration='rebuild01',selected_checkpoint_sha256=plan['checkpoint_sha256'],
        protocol_sha256=sha(W/'protocol/rebuild01_final.json'),completed=len(rows),planned=42,pending_cases=pending,
        final_cases=rows,all_executed_cases=history+rows,earlier_executed_count=len(history),heldout_statistics=stats,
        paired_outcomes=paired,paired_outcome_counts=paired_counts,
        regression_cases=reg,known_failure_cases=known,closed_loop_gate_met=flight,regression_gate_met=regression,
        known_failure_retest_passed=known_ok,color_intervention_gate_met=probe_ok,probe_arithmetic_and_images_verified=probe_checked,
        all_new_records_independently_rescored=verified,execution_audited=execution,preregistered_goal_met=gate,
        role='VLA selects the instructed person through RGB/text-conditioned velocity plans. A decoded plan endpoint is tracked using own odometry; detector only confirms discovery. Instantaneous raw VLA velocities are not directly executed.',
        comparison='Both models use the same plan decoder, own-odometry tracking controller and English prompts. The video retains v1.0 with its original controller and bilingual prompts. These are distinct conditions.',
        limitations=['Same room and two static avatar identities; bounded unseen layouts, not arbitrary environments.',
                    'VLA does not emit a separate person detection label. Recognition is tested through visual/language interventions and target-directed actions.',
                    'The VLA receives stage instructions, not the upper-level Japanese search command.',
                    'The contribution of individual training changes and language adaptation is not isolated.',
                    'Approach velocity is computed by tracking the endpoint encoded in VLA action chunks, with captured/current own-state motion compensation. Do not describe it as raw VLA velocity execution.',
                    'No real aircraft flight or unknown-room claim.'])
    dest=W/'results/all_trials_rebuild01.json';dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['completed','planned','closed_loop_gate_met','regression_gate_met','known_failure_retest_passed','color_intervention_gate_met','preregistered_goal_met']}))
    return result
if __name__=='__main__':main()
