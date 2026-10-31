"""Same physical criteria, explicit primitive provenance, plus fresh VLA stop evidence.

The untouched legacy scorer is run first and its result is retained. Only the
source of arming/landing requests changes with the user-approved role division.
"""
import argparse,contextlib,importlib.util,io,json,os,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def audit(record,scene,search):
    os.environ['RESCUE_PROJECT_ROOT']=str(P);sys.path.insert(0,str(P))
    legacy=load(P/'score_mission.py','legacy_physical_navfocus')
    original=legacy.score(record,scene)
    f=record/'physical_score.json';saved=record/'physical_score_original_contract.json';assert not saved.exists();f.rename(saved)
    rows=[json.loads(s) for s in (record/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    events=read(record/'events.json');profile=original['profile'];result=read(record/'result.json')
    assert result['flight_adapter_revision']=='rebuild03'
    takeoff_request=any(e.get('event')=='mission_takeoff_request' and e.get('source')=='mission_primitive' for e in events)
    land_request=any(e.get('event')=='land_request' and e.get('source')=='mission_primitive' for e in events)
    airborne=bool(-rows[0]['truth'][3]<.1 and original['maximum_height_m']>.85 and takeoff_request)
    if profile in ('blue','red'):
        task=original['goal_holds'][profile]['physical_hold']['duration_s']>=3
        completed=[e for e in events if e.get('event')=='vla_approach_completed' and e.get('phase')==profile]
        vla_stop=any(e['source']=='policy' and e['stop_intent']['source']=='fresh_policy' and e['stop_intent']['valid_state'] for e in completed)
        nav=[r for r in rows if (r.get('execution_owner') or {}).get('owner')=='VLA_plan_tracker']
        preserved=bool(nav) and all(not r['plan_tracking'].get('truth_used',True) and (not r['plan_tracking'].get('valid_plan') or np.allclose(r['plan_tracking']['tracking_request_forward_left'],r['adopted_action'][:2])) for r in nav)
        vla_task_evidence=bool(vla_stop and preserved)
    else:
        task=original['rotations']['left']['completed'] if profile=='left' else all(original['rotations'][p]['completed'] for p in ('right','left'))
        vla_task_evidence=True;preserved=None;vla_stop=None
    physical=bool(airborne and original['explicit_hover_instruction_hold']['duration_s']>=3 and task
                  and original['grounded_disarmed_motors_off'] and land_request and not original['watchdog_landing']
                  and original['minimum_person_clearance_m'] is not None and original['minimum_person_clearance_m']>=.45)
    updated=dict(original)
    updated.update(success=bool(physical and original['learned_policy_provenance'] and vla_task_evidence),takeoff=airborne,
       original_provenance_contract_success=original['success'],primitive_requests=dict(takeoff=takeoff_request,land=land_request),
       vla_approach_completion_fresh=vla_stop,vla_continuous_actions_preserved=False,vla_plan_tracking_provenance=preserved,
       scoring_contract='rebuild03: original physical thresholds unchanged; VLA velocity-plan endpoint tracked using own odometry. Raw instantaneous velocity is not preserved. Fresh VLA stop-plan evidence required.',
       original_contract_record='physical_score_original_contract.json')
    f.write_text(json.dumps(updated,indent=2),encoding='utf-8')
    if search:
        m=load(W/'runtime_navfocus/score_search.py','navfocus_search_score');return m.audit(record,scene)
    return updated
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('record',type=Path);p.add_argument('--scene',required=True,type=Path);p.add_argument('--search',action='store_true');a=p.parse_args();s=audit(a.record,a.scene,a.search);print(json.dumps(dict(success=s['success'])))
