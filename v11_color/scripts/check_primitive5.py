"""Correct a launcher-path omission before freezing the final confirmation."""
import datetime,hashlib,importlib.util,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def main():
    prior=read(W/'runs/rebuild03_dev/summary.json');assert prior['completed']==5
    source=(W/'scripts/run_suite_rebuild03.py').read_text(encoding='utf-8')
    source=source.replace("else P/'vla_worker.py'", "else W/'runtime_rebuild03/vla_worker.py'")
    source=source.replace("assert wr['checkpoint_sha256']==checkpoint_hash", "assert wr['checkpoint_sha256']==checkpoint_hash;assert wr['num_steps']==5")
    path=W/'scripts/run_suite_rebuild03_primitive5.py';path.write_text(source,encoding='utf-8')
    case=dict(id='primitive_blue',kind='primitive',scene='clear',profile='blue',model='v1.1',group='development_worker_path_check')
    plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=[case],
        reason='The prior primitive diagnostic used the original P/vla_worker.py (10 flow steps). Search diagnostics correctly used5. Preserve that run; verify the intended local5-step worker once before final freeze.',
        changes=['Launcher selects runtime_rebuild03/vla_worker.py for primitive flights'],
        unchanged=['Model, runtime, gains, physics, endpoint conversion, thresholds'],runner_sha256=sha(path),runtime_protocol_sha256=sha(W/'protocol/rebuild03_dev.json'))
    write(W/'protocol/rebuild03_primitive5.json',plan)
    spec=importlib.util.spec_from_file_location('runner',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    root=W/'runs/rebuild03_primitive5';root.mkdir(exist_ok=False)
    outcome=mod.run_case(case,W/'models/train16_en/final',root/'primitive_blue_v1.1')
    write(root/'summary.json',dict(cases=[outcome],completed=1,planned=1))
if __name__=='__main__':main()
