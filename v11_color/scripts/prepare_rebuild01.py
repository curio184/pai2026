"""Create a separate development runtime and preregister before any flight."""
import datetime,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1];P=W.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,s):p.write_text(s,encoding='utf-8')
def main():
    src=W/'runtime_navfocus';dest=W/'runtime_rebuild01'
    assert not dest.exists();shutil.copytree(src,dest,ignore=shutil.ignore_patterns('__pycache__'))
    for name in ['plan_endpoint.py','plan_tracker.py']:shutil.copy2(W/'scripts'/name,dest/name)
    for name in ['search_mission.py','ardupilot_bridge/rescue_mission.py']:
        f=dest/name;s=f.read_text(encoding='utf-8')
        s=s.replace('from flight_primitives import flight_action','from flight_primitives import flight_action\nfrom plan_tracker import PlanTracker')
        s=s.replace('horizontal_stabilizer=HorizontalVelocityStabilizer()','horizontal_stabilizer=HorizontalVelocityStabilizer()\n    plan_tracker=PlanTracker();plan_tracking=None;raw_model_action=np.zeros(6)')
        old='                adopted_action,execution_owner=flight_action(phase,own_state,model_action,action_source,t)'
        assert old in s
        s=s.replace(old,'                raw_model_action=model_action.copy()\n                tracked_action,plan_tracking=plan_tracker.update(t,own_state,att.yaw,model_action,model_packet,action_source,phase,prompt)\n                adopted_action,execution_owner=flight_action(phase,own_state,tracked_action,action_source,t)\n                if phase in ("blue","red"):\n                    execution_owner=dict(owner="VLA_plan_tracker",raw_velocity_preserved=False,endpoint_selected_by="VLA",tracking_uses="own_estimated_state_only")')
        s=s.replace('                    model_action[:2],own_state[:2],att.yaw,control_dt,','                    adopted_action[:2],own_state[:2],att.yaw,control_dt,')
        s=s.replace('valid=is_armed and t-stage_start>3 and np.linalg.norm(velocity)<.08','valid=is_armed and t-stage_start>3 and bool(plan_tracking.get("stop_ready"))')
        s=s.replace('stop_window.update(t,model_action[:2],valid,','stop_window.update(t,adopted_action[:2],valid,')
        s=s.replace('                                 horizontal_control=horizontal_control,stop_intent_evidence=stop_window.evidence,','                                 horizontal_control=horizontal_control,stop_intent_evidence=stop_window.evidence,\n                                 plan_tracking=plan_tracking,raw_model_action=raw_model_action.tolist(),')
        s=s.replace('flight_adapter_revision="navfocus"','flight_adapter_revision="rebuild01"')
        write(f,s)
    # A distinct provenance audit preserves all original physical thresholds.
    score=(W/'scripts/score_navfocus.py').read_text(encoding='utf-8')
    score=score.replace("=='navfocus'","=='rebuild01'")
    score=score.replace("=='VLA'","=='VLA_plan_tracker'")
    score=score.replace("preserved=bool(nav) and all(np.array_equal(np.asarray(r['model_action'])[:4],np.asarray(r['adopted_action'])[:4]) for r in nav)","preserved=bool(nav) and all(not r['plan_tracking'].get('truth_used',True) and (not r['plan_tracking'].get('valid_plan') or np.allclose(r['plan_tracking']['tracking_request_forward_left'],r['adopted_action'][:2])) for r in nav)")
    score=score.replace("vla_continuous_actions_preserved=preserved","vla_continuous_actions_preserved=False,vla_plan_tracking_provenance=preserved")
    score=score.replace("navfocus: unchanged physical thresholds; honestly recorded planned primitive requests; fresh VLA stop intent required for approach.","rebuild01: original physical thresholds unchanged; VLA velocity-plan endpoint tracked using own odometry. Raw instantaneous velocity is not preserved. Fresh VLA stop-plan evidence required.")
    write(W/'scripts/score_rebuild01.py',score)
    runner=(W/'scripts/run_suite_receipt.py').read_text(encoding='utf-8')
    start=runner.index('def lock_check():');end=runner.index('\ndef run_case(',start)
    runner=runner[:start]+'''def lock_check():
    lock=json.loads((W/'protocol/rebuild01_dev.json').read_text())
    for n,h in lock['runtime_sha256'].items():assert sha(W/'runtime_rebuild01'/n)==h,n
    assert sha(W/'scripts/score_rebuild01.py')==lock['score_sha256']
    return lock
'''+runner[end:]
    runner=runner.replace("W/'runtime_navfocus/", "W/'runtime_rebuild01/")
    runner=runner.replace("str(P/'vla_worker.py')","str(W/'runtime_rebuild01/vla_worker.py')")
    runner=runner.replace("'--chunk-origin','receipt'","'--chunk-origin','split'")
    runner=runner.replace("W/'scripts/score_navfocus.py'","W/'scripts/score_rebuild01.py'")
    runner=runner.replace("W/'protocol/navfocus_receipt.json'","W/'protocol/rebuild01_dev.json'")
    write(W/'scripts/run_suite_rebuild01.py',runner)
    # Primitive worker imports its adapter from the separate runtime.
    shutil.copy2(P/'vla_worker.py',dest/'vla_worker.py')
    prior=read(W/'protocol/navfocus_receipt.json')
    ids=['NFH01','NFH04','NFH13']
    cases=[next(c for c in prior['cases'] if c['id']==i and c['model']=='v1.1') for i in ids]
    for c in cases:c['group']='development_existing_diagnostic_layout'
    plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope='Development only. Three preselected existing diagnostic conditions, no final holdout claim. No training or weight selection.',
        hypothesis='Execute a VLA-predicted stopping endpoint with own-odometry delay compensation rather than replay an obsolete velocity sequence.',
        changed=['VLA plan endpoint decoding/tracking','Own-state completion additionally requires fresh VLA stop plan and low speed'],
        unchanged=['Model train16 final','All physical scoring thresholds','PI gains','Rendered scene and camera','Instruction language','WSL4CPU/8GiB'],
        endpoint_tracker=dict(position_gain=.8,velocity_damping=.5,endpoint_smoothing=.5,stop_error_m=.08,stop_speed_m_s=.05),
        candidate=prior['candidate'],checkpoint_sha256=prior['checkpoint_sha256'],cases=cases,
        runtime_sha256={p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file()},
        score_sha256=sha(W/'scripts/score_rebuild01.py'),runner_sha256=sha(W/'scripts/run_suite_rebuild01.py'))
    with (W/'protocol/rebuild01_dev.json').open('x',encoding='utf-8') as f:json.dump(plan,f,indent=2)
    print(json.dumps(dict(runtime=str(dest),preregistered_cases=ids)))
if __name__=='__main__':main()
