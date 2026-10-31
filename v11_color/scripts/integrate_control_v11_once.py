"""Create the separately authorized v1.1 control runtime; preserve originals."""
from pathlib import Path
import ast,datetime,hashlib,json,shutil

W=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def once(text,a,b):
    assert text.count(a)==1,repr(a)
    return text.replace(a,b)

def main():
    source=W/'runtime_english';target=W/'runtime_control_v11'
    assert not (W/'protocol/runtime_control_v11_lock.json').exists()
    original={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    for relative,h in original.items():
        destination=target/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source/relative,destination)
    module=(W/'design_review/velocity_stabilizer.py').read_text(encoding='utf-8')
    module=module.replace('This module is NOT used by any recorded or currently running flight.',
                          'This revision is integrated only into runtime_control_v11; old runtimes are preserved.')
    module=module.replace('integrated_into_runtime=False,','controller_revision="control_v11",')
    (target/'velocity_stabilizer.py').write_text(module,encoding='utf-8')
    shutil.copy2(W/'design_review/stop_intent.py',target/'stop_intent.py')
    for relative in ('search_mission.py','ardupilot_bridge/rescue_mission.py'):
        p=target/relative;text=p.read_text(encoding='utf-8')
        if relative=='search_mission.py':
            text=once(text,'sys.path.insert(0,os.environ["RESCUE_PROJECT_ROOT"])',
                      'sys.path.insert(0,os.environ["RESCUE_PROJECT_ROOT"])\nsys.path.insert(0,str(Path(__file__).resolve().parent))')
        else:
            assert 'sys.path.insert(0,str(Path(__file__).resolve().parents[1]))' in text
        text=once(text,'from flight_progress import StopCommandWindow',
                  'from stop_intent import StopIntentWindow\nfrom velocity_stabilizer import HorizontalVelocityStabilizer')
        text=once(text,'model_action=np.zeros(6);action_source="initializing";own_state=None',
                  'model_action=np.zeros(6);action_source="initializing";own_state=None\n    horizontal_stabilizer=HorizontalVelocityStabilizer()\n    horizontal_control=None')
        text=once(text,'stop_window=StopCommandWindow()','stop_window=StopIntentWindow()')
        old='''                desired=np.array([model_action[0],-model_action[1]])
                accel = np.clip(desired-velocity,-.8,.8)
                roll = math.atan2(accel[1],9.81)
                pitch = -math.atan2(accel[0],9.81)'''
        new='''                horizontal_control=horizontal_stabilizer.update(
                    model_action[:2],own_state[:2],att.yaw,control_dt,
                    armed=is_armed,stationary_requested=phase not in ("blue","red"))
                roll=horizontal_control["roll_rad"]
                pitch=horizontal_control["pitch_rad"]'''
        text=once(text,old,new)
        text=once(text,'valid=is_armed and t-stage_start>3 and np.linalg.norm(velocity)<.08 and action_source=="policy"',
                  'valid=is_armed and t-stage_start>3 and np.linalg.norm(velocity)<.08')
        text=once(text,'stop_window.update(t,model_action[:2],valid)',
                  'stop_window.update(t,model_action[:2],valid,source=action_source,instruction=prompt)')
        text=once(text,'model_action=model_action.tolist(),action_source=action_source,estimated_state=own_state,',
                  'model_action=model_action.tolist(),action_source=action_source,estimated_state=own_state,\n                                 horizontal_control=horizontal_control,stop_intent_evidence=stop_window.evidence,')
        ast.parse(text,filename=str(p));p.write_text(text,encoding='utf-8')
    # Keep every old source and score byte-identical. No changes to firmware,
    # plant, detector, model inference, yaw/vertical channels or score criteria.
    for relative,h in original.items():assert sha(source/relative)==h,relative
    for name in ('score_mission.py','score_search.py','confirmation.py','perception.py','search_link.py','smolvla_policy.py'):
        assert sha(source/name)==sha(target/name),name
    lock=json.loads((W/'protocol/runtime_english_lock.json').read_text())
    lock['runtime']={p.relative_to(target).as_posix():sha(p) for p in target.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    lock['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    lock['authorization']='User explicitly approved v1.1-side control changes and a2.5hour work window; old runtime and scoring preserved.'
    lock['changes']=['20Hz horizontal PI, kp1 ki.25, prior acceleration and velocity limits',
                     'Explicit stationary phases request zero horizontal velocity; VLA owns approach requests',
                     'Short stale_hover gaps<=.5s preserve remembered stop intent only; completion requires fresh policy and unchanged command window',
                     'Separate logging of VLA requests, adopted requests, integral/attitude commands and stop-intent evidence']
    lock['stop_intent_rationale']='H09 was physically stopped but repeated brief stale_hover events reset progress. Stale actions are still rejected for execution. No stale packet can complete the task. No physical acceptance threshold is relaxed.'
    (W/'protocol/runtime_control_v11_lock.json').write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8')
    runner=(W/'scripts/run_suite_bounded.py').read_text(encoding='utf-8').replace('runtime_english','runtime_control_v11')
    ast.parse(runner)
    (W/'scripts/run_suite_control_v11.py').write_text(runner,encoding='utf-8')
    receipt=dict(created_utc=lock['created_utc'],original_runtime_files_unchanged=len(original),
                 new_runtime=str(target),new_runtime_lock_sha256=sha(W/'protocol/runtime_control_v11_lock.json'),
                 new_runner_sha256=sha(W/'scripts/run_suite_control_v11.py'),
                 original_scorers_unchanged=True,no_flight_started=True,no_training_started=True,
                 coefficients_selected_by='single ideal continuous design (s+.5)^2; no gain search; actual full-system success unverified')
    (W/'reports/control_v11_integration_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))

if __name__=='__main__':main()
