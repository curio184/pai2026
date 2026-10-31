"""Attribute failed physical checks from immutable flight traces, postflight only."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(a):return np.percentile(a,[0,50,100]).tolist() if len(a) else None
def main():
    p=argparse.ArgumentParser();p.add_argument('--suite',default='heldout_train03');a=p.parse_args()
    folder=W/'runs'/a.suite;summary=read(folder/'summary.json');rows=[]
    for outcome in summary['cases']:
        case=outcome['case'];record=folder/(case['id']+'_'+case['model'])/'record'
        if not (record/'search_score.json').exists():continue
        score=read(record/'search_score.json');physical=score['physical'];result=read(record/'result.json')
        trace=[json.loads(line) for line in (record/'trace.jsonl').read_text().splitlines()]
        phases={}
        for phase in ['takeoff','hover','right','left','confirm','reacquire','blue','red','report','land']:
            rr=[r for r in trace if r['phase']==phase and r.get('estimated_state') is not None]
            if not rr:continue
            truth=np.asarray([r['truth'] for r in rr]);own=np.asarray([r['estimated_state'] for r in rr]);commands=np.asarray([r['model_action'] for r in rr])
            speed=np.linalg.norm(truth[:,4:6],axis=1);height=-truth[:,3];vertical=np.abs(truth[:,6])
            phases[phase]=dict(start=rr[0]['t'],end=rr[-1]['t'],samples=len(rr),
                physical_height_min_median_max=stats(height),estimated_altitude_min_median_max=stats(own[:,3]),
                physical_horizontal_speed_min_median_max=stats(speed),estimated_horizontal_speed_min_median_max=stats(np.linalg.norm(own[:,:2],axis=1)),
                physical_vertical_speed_abs_min_median_max=stats(vertical),median_model_action=np.median(commands,axis=0).tolist(),
                fraction_physical_speed_within_limit=float((speed<=.08).mean()),
                fraction_physical_height_within_limit=float(((height>=.8)&(height<=1.25)).mean()),
                fraction_physical_vertical_speed_within_limit=float((vertical<=.08).mean()))
        color=case['color'];holds=physical['goal_holds'][color]
        components=dict(learned_policy=physical['learned_policy_provenance'],takeoff=physical['takeoff'],
            initial_hover_3s=physical['explicit_hover_instruction_hold']['duration_s']>=3,
            target_hold_3s=holds['physical_hold']['duration_s']>=3,
            grounded=physical['grounded_disarmed_motors_off'],policy_land=physical['policy_requests']['land'],
            no_watchdog=not physical['watchdog_landing'],person_clearance=physical['minimum_person_clearance_m'] is not None and physical['minimum_person_clearance_m']>=.45)
        assert all(components.values())==physical['success'],('Diagnostic does not reproduce frozen physical score',case['id'])
        rows.append(dict(case=case,success=score['success'],mission_failure=result.get('mission_failure'),
            approach_hold_s=holds['physical_hold']['duration_s'],minimum_goal_distance_m=holds['minimum_goal_distance_m'],
            explicit_hover_hold_s=physical['explicit_hover_instruction_hold']['duration_s'],minimum_person_clearance_m=physical['minimum_person_clearance_m'],
            failed_checks=[k for k,v in score['checks'].items() if not v],
            failed_physical_components=[k for k,v in components.items() if not v],phases=phases,
            trace_sha256=sha(record/'trace.jsonl'),score_sha256=sha(record/'search_score.json')))
    output=dict(suite=a.suite,completed=summary['completed'],planned=summary['planned'],cases=rows,
                scope='Offline attribution of physical checks. Truth is not supplied to a model, detector or mission controller. Correlations do not identify a unique cause.',
                caveat='Estimated states here are controller-time logs; exact image-time model inputs are separately preserved in vla_link_events.json.')
    output['component_counts']={}
    for model in ['v1.0','v1.1']:
        chosen=[r for r in rows if r['case']['model']==model]
        output['component_counts'][model]=dict(completed=len(chosen),mission_success=sum(r['success'] for r in chosen),
            requested_goal_hold_at_least_3s=sum(r['approach_hold_s']>=3 for r in chosen),
            initial_hover_at_least_3s=sum(r['explicit_hover_hold_s']>=3 for r in chosen),
            search_rotation_pass=sum('search_rotation_completed' not in r['failed_checks'] for r in chosen),
            note='Component outcomes diagnose failures; they do not replace the preregistered full-mission success gate.')
    dest=W/'reports'/(a.suite+'_phase_diagnostic.json');dest.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(completed=output['completed'],planned=output['planned'],failed_v11=[r['case']['id'] for r in rows if r['case']['model']=='v1.1' and not r['success']],path=str(dest)),ensure_ascii=False))
if __name__=='__main__':main()
