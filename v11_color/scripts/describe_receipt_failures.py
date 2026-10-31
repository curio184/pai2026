"""Postflight explanation of every failed fixed trial; does not change scores."""
import hashlib,json
from pathlib import Path
import numpy as np

W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    plan=read(W/'protocol/navfocus_receipt.json');failures=[];completed=0
    for case in plan['cases']:
        folder=W/'runs/navfocus_receipt'/(case['id']+'_'+case['model'])
        if not (folder/'outcome.json').exists():continue
        out=read(folder/'outcome.json');completed+=1
        if out['success']:continue
        record=folder/'record';p=read(record/'physical_score.json');target=case.get('color',case.get('profile'))
        result=read(record/'result.json');reasons=[]
        if not p['takeoff']:reasons.append('takeoff')
        if p['explicit_hover_instruction_hold']['duration_s']<3:reasons.append('initial_hover_under_3s')
        if not p['grounded_disarmed_motors_off']:reasons.append('not_grounded_disarmed')
        if p['watchdog_landing']:reasons.append('watchdog_landing')
        if p['minimum_person_clearance_m'] is None or p['minimum_person_clearance_m']<.45:reasons.append('person_clearance')
        if not all(p['primitive_requests'].values()):reasons.append('primitive_request_provenance')
        target_details=None
        if target in ('blue','red'):
            g=p['goal_holds'][target];hold=g['physical_hold']['duration_s']
            if hold<3:reasons.append('target_region_low_speed_hold_under_3s')
            if not p['vla_approach_completion_fresh']:reasons.append('no_fresh_vla_stop_completion')
            if not p['vla_continuous_actions_preserved']:reasons.append('vla_actions_not_preserved')
            rows=[json.loads(s) for s in (record/'trace.jsonl').open(encoding='utf-8')]
            nav=[r for r in rows if (r.get('execution_owner') or {}).get('owner')=='VLA']
            target_details=dict(hold_s=hold,minimum_goal_distance_m=g['minimum_goal_distance_m'],
                other_goal_minimum_m=p['goal_holds']['red' if target=='blue' else 'blue']['minimum_goal_distance_m'],
                navigation_rows=len(nav))
            if nav:
                last=nav[-1];truth=np.asarray(last['truth']);xy=truth[[2,1]]
                target_details.update(last_vla_time_s=last['t'],last_vla_goal_distance_m=float(np.linalg.norm(xy-g['goal_scene_xy_m'])),
                    last_vla_horizontal_speed_m_s=float(np.linalg.norm(truth[4:6])),last_vla_height_m=float(-truth[3]),
                    last_vla_action=last['model_action'],last_vla_source=last['action_source'])
            inf=[r for r in read(record/'vla_link_events.json') if r['event']=='inference' and f'wearing {target}' in r['instruction']]
        else:
            for phase in (['left'] if target=='left' else ['right','left']):
                if not p['rotations'][phase]['completed']:reasons.append(phase+'_rotation')
            inf=[]
        if case['kind']=='search':
            reasons.extend(k for k,v in read(record/'search_score.json')['checks'].items() if not v and k!='physical_flight')
        evidence=None
        if inf:
            last=inf[-1];image=record/'observations'/last['image_file']
            assert sha(image)==last['image_sha256']
            evidence=dict(image=image.relative_to(W).as_posix(),image_sha256=sha(image),
                instruction=last['instruction'],capture_time_s=last['sim_time_capture'],action=last['action'],
                estimated_state=last['estimated_state'])
        failures.append(dict(case=case,reasons=reasons,target=target_details,evidence=evidence,
            stop_reason=result['stop_reason'],mission_failure=result.get('mission_failure'),
            record=folder.relative_to(W).as_posix(),score_sha256=sha(record/'physical_score.json')))
    report=dict(scope='Postflight description, all failed fixed cases; no tuning or rescore changes',completed=completed,
        planned=42,failures=failures,successes=completed-len(failures))
    (W/'reports/receipt_failure_details.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(completed=completed,failed=len(failures))))
if __name__=='__main__':main()
