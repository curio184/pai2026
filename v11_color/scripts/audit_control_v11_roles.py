"""Source-boundary audit, separate from behavioral success evidence."""
import hashlib,json,importlib.machinery
from pathlib import Path
W=Path(__file__).resolve().parents[1];P=W.parent;R=W/'runtime_control_v11'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def excerpt(p,needle,padding=2):
    lines=p.read_text(encoding='utf-8').splitlines();hits=[i for i,s in enumerate(lines) if needle in s]
    assert hits,(p,needle)
    return [dict(start_line=max(0,i-padding)+1,end_line=min(len(lines),i+padding+1),text='\n'.join(lines[max(0,i-padding):min(len(lines),i+padding+1)])) for i in hits]
def main():
    lock=json.loads((W/'protocol/runtime_control_v11_lock.json').read_text())
    assert all(sha(R/n)==h for n,h in lock['runtime'].items())
    assert all(sha(P/n)==h for n,h in lock['project_imports'].items())
    dependencies={}
    for module in ('smolvla_policy','perception','vla_link'):
        spec=importlib.machinery.PathFinder.find_spec(module,[str(P),str(R)])
        assert spec and spec.origin
        path=Path(spec.origin);dependencies[module]=dict(path=str(path),sha256=sha(path))
        if module in ('smolvla_policy','vla_link'):assert sha(path)==lock['project_imports'][module+'.py']
        if module=='perception':assert sha(path)==lock['runtime']['perception.py']
    items=[
      ('policy_before_detector','search_worker.py','chunk=policy.infer_chunk',
       'Policy input is RGB + instruction + estimated state. Person detection runs independently after this call.'),
      ('policy_packet','search_link.py','request=dict(version=1',
       'The policy request contains JPEG, estimated state and instruction; qpos/qvel remain on the rendering side.'),
      ('own_state','search_mission.py','own_state=[',
       'Nine input state components are from autopilot estimates and armed state, not target coordinates.'),
      ('horizontal_execution','search_mission.py','horizontal_control=horizontal_stabilizer.update',
       'Blue/red approach phases execute bounded VLA horizontal requests. Other phases explicitly request stationary horizontal motion.'),
      ('approach_completion','search_mission.py','navigation_complete=stop_window.update',
       'Approach completion requires stop-command intent and independent target confirmation; it does not use postflight goal distance.'),
      ('physical_execution','velocity_stabilizer.py','def update(',
       'Velocity stabilizer accepts only requested/estimated velocity, own yaw/time/armed state and stationary request; no target/color/image input.'),
      ('stop_intent','stop_intent.py','return bool(held and fresh)',
       'Completion requires a fresh model output; brief stale gaps remember intent only, never execute the remembered command.')]
    rows=[]
    for key,file,needle,meaning in items:
        p=R/file;rows.append(dict(boundary=key,path=p.relative_to(W).as_posix(),sha256=sha(p),meaning=meaning,evidence=excerpt(p,needle)))
    obj=dict(runtime_lock_sha256=sha(W/'protocol/runtime_control_v11_lock.json'),passed=True,dependencies=dependencies,boundaries=rows,
      meaning_of_recognition='Choosing the instructed person through generated motion, tested by image/language interventions; not a separate person classification output.',
      limitations='This audit proves the inspected interfaces and source boundaries, not correct target selection or mission success. Behavioral evidence must independently pass.',
      legacy_metadata_note='Inherited language-only fields in the runtime lock describe its parent. Current changes are in changes[] and actual file hashes. controller_source_modified:false in flight results refers to the ArduPilot firmware, not unchanged Python velocity control.')
    dest=W/'reports/control_v11_role_source_audit.json';dest.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,boundaries=len(rows),resolved_modules=dependencies),ensure_ascii=False))
if __name__=='__main__':main()
