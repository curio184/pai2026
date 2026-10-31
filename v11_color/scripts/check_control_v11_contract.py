"""Code contract checks before the single registered final evaluation."""
from pathlib import Path
import ast,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parents[1]
R=W/'runtime_control_v11'
sys.path.insert(0,str(R))
from stop_intent import StopIntentWindow
from velocity_stabilizer import HorizontalVelocityStabilizer

def main():
    checks=[]
    window=StopIntentWindow()
    outcomes=[]
    for i in range(1,101):
        t=i*.05;source='stale_hover' if 2.<=t<=2.2 else 'policy'
        outcomes.append(window.update(t,[0.,0.],True,source=source,instruction='approach blue'))
        if source=='stale_hover':assert not outcomes[-1]
    assert outcomes[-1]
    checks.append('brief_stale_hover_preserves_intent_but_cannot_complete')
    window=StopIntentWindow()
    for i in range(1,101):
        t=i*.05
        completed=window.update(t,[.15,0.],True,source='policy' if t<2 else 'stale_hover',instruction='approach blue')
        assert not completed
    checks.append('moving_intent_not_replaced_by_safety_hover_zero')
    window=StopIntentWindow()
    for i in range(1,101):
        t=i*.05;source='policy' if t<2 else 'stale_hover'
        assert not window.update(t,[0.,0.],True,source=source,instruction='approach blue')
    assert window.evidence['source']=='invalid'
    checks.append('long_stale_gap_invalidates_progress')
    window=StopIntentWindow()
    for i in range(1,101):
        t=i*.05;prompt='blue' if t<3 else 'red'
        assert not window.update(t,[0.,0.],True,source='policy',instruction=prompt)
    checks.append('instruction_change_resets_intent_window')
    for name in ['search_mission.py','ardupilot_bridge/rescue_mission.py','velocity_stabilizer.py','stop_intent.py']:
        tree=ast.parse((R/name).read_text(encoding='utf-8'))
        if name.endswith('rescue_mission.py') or name=='search_mission.py':
            calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='horizontal_stabilizer']
            assert len(calls)==1
            names={n.id for n in ast.walk(calls[0]) if isinstance(n,ast.Name)}
            assert not names & {'state','truth','persons','targets','scene','visual','confirmed'}
    checks.append('horizontal_controller_call_has_no_target_image_or_truth_arguments')
    c=HorizontalVelocityStabilizer()
    r=c.update([.12,0.],[0.,0.],0.,.05,armed=True,stationary_requested=False)
    assert r['adopted_requested_forward_left']==[.12,0.] and r['pitch_rad']<0
    checks.append('approach_preserves_vla_velocity_request')
    r=c.update([.12,0.],[0.,0.],0.,.05,armed=True,stationary_requested=True)
    assert r['raw_requested_forward_left']==[.12,0.] and r['adopted_requested_forward_left']==[0.,0.]
    checks.append('stationary_override_and_raw_request_logged_separately')
    for name in ['score_mission.py','score_search.py','perception.py','confirmation.py','search_link.py','smolvla_policy.py']:
        assert (R/name).read_bytes()==(W/'runtime_english'/name).read_bytes()
    checks.append('scorers_detector_model_inference_and_action_freshness_limits_unchanged')
    report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,
                checks=checks,source_contract_check='design_review/code_contract_checks.json',
                runtime_lock_sha256=hashlib.sha256((W/'protocol/runtime_control_v11_lock.json').read_bytes()).hexdigest(),
                scope='Deterministic code checks only; no dynamics rollout, VLA inference, gain selection or flight-success claim.')
    with (W/'reports/control_v11_contract_checks.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))

if __name__=='__main__':main()
