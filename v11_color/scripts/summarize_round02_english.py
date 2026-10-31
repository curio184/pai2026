"""Keep failed round 1 separate; summarize the English final candidate and all trials."""
import argparse,hashlib,json,math
from pathlib import Path
from run_round02_english import stress_pass
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wilson(k,n):
    if not n:return None
    z=1.959963984540054;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;r=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [c-r,c+r]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--candidate',default='train04_en');a=parser.parse_args()
    selection=W/'protocol/selected_final_round02_english.json';selected=read(selection) if selection.exists() else None
    candidate=selected['candidate'] if selected else a.candidate
    base=read(W/'protocol/plan.json');plan=read(W/'protocol/round02_english.json')
    allrows=[];notrun=[];planned_keys=set()
    for suite in sorted((W/'runs').iterdir()):
        if not (suite/'suite_plan.json').exists():continue
        for case in read(suite/'suite_plan.json')['cases']:
            planned_keys.add((suite.name,case['id'],case['model']))
            folder=suite/(case['id']+'_'+case['model']);row=dict(suite=suite.name,case=case,record=folder.relative_to(W).as_posix())
            if not (folder/'outcome.json').exists():notrun.append(row);continue
            outcome=read(folder/'outcome.json');row.update(success=outcome['success'],error=outcome.get('error'),flight_started=outcome['flight_started'],checkpoint_sha256=outcome.get('checkpoint_sha256'))
            f=folder/'record'/('search_score.json' if case['kind']=='search' else 'physical_score.json')
            if f.exists():
                score=read(f);physical=score['physical'] if case['kind']=='search' else score;target=case.get('color',case.get('profile'))
                if target in ['blue','red']:
                    goal=physical['goal_holds'][target];row.update(hold_s=goal['physical_hold']['duration_s'],min_goal_distance_m=goal['minimum_goal_distance_m'],other_min_goal_distance_m=physical['goal_holds']['red' if target=='blue' else 'blue']['minimum_goal_distance_m'])
                row.update(min_person_clearance_m=physical.get('minimum_person_clearance_m'),score_path=f.relative_to(W).as_posix(),score_sha256=sha(f))
            f=folder/'record/result.json'
            if f.exists():
                r=read(f);row.update(stop_reason=r['stop_reason'],mission_failure=r.get('mission_failure'))
            allrows.append(row)
    expected=[]
    for l in base['development_layouts']:
        for color in ['blue','red']:expected.append(('dev',dict(id=l['name']+'_'+color,kind='search',scene=l['name'],color=color,model='v1.1')))
    for profile in ['blue','red','turns','left']:expected.append(('dev',dict(id='primitive_'+profile,kind='primitive',scene='clear',profile=profile,model='v1.1')))
    expected.extend(('stress',dict(c)) for c in plan['development_stress_cases'])
    for scene,color in [('clear','blue'),('clear','red'),('fog_light','blue'),('fog_dense','blue'),('dust','blue')]:expected.append(('regression',dict(id=scene+'_'+color,kind='search',scene=scene,color=color,model='v1.1')))
    expected.append(('known_failure',dict(id='T3_blue_retest',kind='search',scene='known_swapped',color='blue',model='v1.1')))
    for c in plan['heldout_cases']:
        for model in ['v1.0','v1.1']:expected.append(('heldout_round02_english',dict(**c,kind='search',model=model,jitter=True)))
    for prefix,case in expected:
        suite=prefix+'_'+candidate
        if (suite,case['id'],case['model']) not in planned_keys:notrun.append(dict(suite=suite,case=case,reason='Conditional stage not started; preregistered gates apply'))
    final_suite='heldout_round02_english_'+candidate
    heldout=[r for r in allrows if r['suite']==final_suite];stats=[]
    for model in ['v1.0','v1.1']:
        for group,key in [('all',None),('color','blue'),('color','red')]+[('layout',l['name']) for l in plan['heldout_layouts']]:
            rows=[r for r in heldout if r['case']['model']==model and (group=='all' or r['case']['color' if group=='color' else 'scene']==key)]
            k=sum(r['success'] for r in rows);n=len(rows);stats.append(dict(model=model,group=group,key=key,k=k,n=n,wilson95=wilson(k,n)))
    v=[s for s in stats if s['model']=='v1.1'];flight=bool(selected and len(heldout)==32 and v[0]['n']==16 and v[0]['k']>=14 and all(s['n']==8 and s['k']>=7 for s in v if s['group']=='color') and all(s['n']==4 and s['k']>=3 for s in v if s['group']=='layout'))
    reg=[r for r in allrows if r['suite']=='regression_'+candidate or r['suite']=='dev_'+candidate and r['case']['kind']=='primitive']
    known=[r for r in allrows if r['suite']=='known_failure_'+candidate]
    dev=[r for r in allrows if r['suite']=='dev_'+candidate]
    stressfile=W/'runs'/('stress_'+candidate)/'summary.json'
    development=bool(len(dev)==8 and all(r['success'] for r in dev) and stressfile.exists() and stress_pass(read(stressfile)))
    regression=bool(len(reg)==9 and all(r['success'] for r in reg));known_gate=bool(len(known)==1 and known[0]['success'])
    probe_gate=False;probe_consistent=False;probe_path=W/'probe_round02_english/outputs/summary.json'
    if probe_path.exists():
        proof_file=W/'reports/probe_consistency_verification.json'
        def current_proof():
            if not proof_file.exists():return False
            proofs=read(proof_file)
            return proofs['all_consistent'] and any(p['probe']=='round02_english' and p['summary_sha256']==sha(probe_path)
                and p['raw_sha256']==sha(probe_path.parent/'raw_outputs.jsonl')
                and selected and p['selected_checkpoint_sha256']==selected['checkpoint_sha256'] for p in proofs['probes'])
        if not current_proof():
            from verify_probe_consistency import main as verify_probes
            verify_probes()
        probe_consistent=bool(current_proof())
        q=next(p for p in read(probe_path)['summary'] if p['model']=='v1.1' and p['prompt_group']=='runtime_english')
        probe_gate=q['outputs']==64 and q['correct_goal']>=60 and q['quartets']==16 and q['whole_quartet_correct']>=14
    verification=W/'reports'/(candidate+'_all_records_verified.json')
    verified=bool(verification.exists() and read(verification)['evidence_consistent'] and read(verification)['records']==len(allrows))
    current_missing=[r for r in notrun if r['suite'].endswith('_'+candidate)]
    from verify_runtime_instructions import main as verify_instructions
    instruction_proof=verify_instructions()
    current_case_paths={r['record'] for r in allrows if r['suite'].endswith('_'+candidate)}
    instruction_checked={r['record'] for r in instruction_proof['cases'] if r['checked']}
    instructions_verified=bool(current_case_paths and current_case_paths.issubset(instruction_checked))
    gate=bool(flight and development and regression and known_gate and probe_gate and probe_consistent and verified and instructions_verified and not current_missing)
    result=dict(candidate=candidate,selected_checkpoint_sha256=selected['checkpoint_sha256'] if selected else None,
        prompt_language='English',round_protocol_sha256=sha(W/'protocol/round02_english.json'),
        all_executed_cases=allrows,not_executed_cases=notrun,heldout_statistics=stats,regression_cases=reg,known_failure_cases=known,
        preregistered_goal_met=gate,closed_loop_gate_met=flight,development_gate_met=development,regression_gate_met=regression,
        color_intervention_gate_met=probe_gate,probe_arithmetic_and_images_verified=probe_consistent,known_failure_retest_passed=known_gate,all_records_independently_rescored=verified,actual_english_instructions_verified=instructions_verified,
        earlier_failed_final_round=dict(candidate='train03',prompt_language='Bilingual English/Japanese',
            report='reports/heldout_train03_round_summary.json',report_sha256=sha(W/'reports/heldout_train03_round_summary.json'),
            v10_successes=2,v11_successes=6,trials_per_model=16,retained=True,pooled_with_new_round=False),
        english_transition_probe=dict(report='probe_english_transition/outputs/summary.json',report_sha256=sha(W/'probe_english_transition/outputs/summary.json'),scope='Exposed round-1 views, completed train03 model; development diagnostic only'),
        limits=['Same room, two static avatar identities, bounded layout distribution.','English stage instructions; the Japanese high-level mission command is handled by the mission manager, not directly by the VLA.','Failed first final round informed subsequent development; only round 2 is untouched for the final selected candidate.','No unknown rooms, moving people or real aircraft flight claims.'],
        video_model='v1.0, bilingual stage prompts, unchanged')
    dest=W/'results/all_trials_round02_english.json';dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(candidate=candidate,executed=len(allrows),not_executed=len(notrun),goal_met=gate,selected=bool(selected))))
if __name__=='__main__':main()
