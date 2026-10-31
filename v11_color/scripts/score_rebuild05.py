"""Score rebuild05 records (latency 0.2 s; otherwise as rebuild04) with the same physical criteria as rebuild03.

Differences from score_rebuild03.py:
- flight_adapter_revision must be 'rebuild04' (fixed 0.4 s latency, no plan tracker)
- VLA evidence: during the approach phase, the executed horizontal command equals the
  time-aligned VLA chunk step (raw_velocity_preserved), and every delivery happened
  0.40-0.45 s after capture.
Physical thresholds (hover, 25 cm / 0.08 m/s / 3 s stop, clearance, landing) are unchanged.
"""
import argparse,importlib.util,json,os,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def audit(record,scene,search):
    os.environ['RESCUE_PROJECT_ROOT']=str(P);sys.path.insert(0,str(P))
    legacy=load(P/'score_mission.py','legacy_physical_rebuild05')
    original=legacy.score(record,scene)
    f=record/'physical_score.json';saved=record/'physical_score_original_contract.json'
    f.replace(saved)
    rows=[json.loads(s) for s in (record/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    events=read(record/'events.json');profile=original['profile'];result=read(record/'result.json')
    assert result['flight_adapter_revision']=='rebuild05' and result['plan_tracker_used'] is False;L=float(result['fixed_latency_s']);assert abs(L-.2)<1e-9
    deliveries=read(record/'latency_deliveries.json')['deliveries']
    ages=[d['delivery_age_s'] for d in deliveries]
    latency_ok=bool(ages) and min(ages)>=L-1e-6 and max(ages)<=L+.05+1e-6
    takeoff_request=any(e.get('event')=='mission_takeoff_request' and e.get('source')=='mission_primitive' for e in events)
    land_request=any(e.get('event')=='land_request' and e.get('source')=='mission_primitive' for e in events)
    airborne=bool(-rows[0]['truth'][3]<.1 and original['maximum_height_m']>.85 and takeoff_request)
    if profile in ('blue','red'):
        task=original['goal_holds'][profile]['physical_hold']['duration_s']>=3
        completed=[e for e in events if e.get('event')=='vla_approach_completed' and e.get('phase')==profile]
        vla_stop=any(e['source']=='policy' and e['stop_intent']['source']=='fresh_policy' and e['stop_intent']['valid_state'] for e in completed)
        nav=[r for r in rows if (r.get('execution_owner') or {}).get('owner')=='VLA' and r.get('action_source')=='policy']
        preserved=bool(nav) and all(np.allclose(r['adopted_action'][:4],r['raw_model_action'][:4]) for r in nav)
        vla_task_evidence=bool(vla_stop and preserved)
    else:
        task=original['rotations']['left']['completed'] if profile=='left' else all(original['rotations'][p]['completed'] for p in ('right','left'))
        vla_task_evidence=True;preserved=None;vla_stop=None
    physical=bool(airborne and original['explicit_hover_instruction_hold']['duration_s']>=3 and task
                  and original['grounded_disarmed_motors_off'] and land_request and not original['watchdog_landing']
                  and original['minimum_person_clearance_m'] is not None and original['minimum_person_clearance_m']>=.45)
    updated=dict(original)
    updated.update(success=bool(physical and original['learned_policy_provenance'] and vla_task_evidence and latency_ok),takeoff=airborne,
       original_provenance_contract_success=original['success'],primitive_requests=dict(takeoff=takeoff_request,land=land_request),
       vla_approach_completion_fresh=vla_stop,vla_continuous_actions_preserved=preserved,
       fixed_latency=dict(ok=latency_ok,deliveries=len(ages),min_age_s=min(ages) if ages else None,max_age_s=max(ages) if ages else None,median_age_s=float(np.median(ages)) if ages else None),
       scoring_contract='rebuild04: original physical thresholds unchanged; VLA chunk step executed unchanged with fixed 0.2 s simulated latency.',
       original_contract_record='physical_score_original_contract.json')
    f.write_text(json.dumps(updated,indent=2),encoding='utf-8')
    if search:
        m=load(W/'runtime_navfocus/score_search.py','navfocus_search_score_r05');return m.audit(record,scene)
    return updated
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('record',type=Path);p.add_argument('--scene',required=True,type=Path);p.add_argument('--search',action='store_true');a=p.parse_args();s=audit(a.record,a.scene,a.search);print(json.dumps(dict(success=s['success'])))
