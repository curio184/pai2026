"""Use the preregistered five-step flow choice with the unchanged pipeline/controller."""
import ast,datetime,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    benchmark=read(W/'reports/flow_steps_benchmark01.json');assert benchmark['selected_steps']==5
    dest=W/'runtime_rebuild03';assert not dest.exists()
    shutil.copytree(W/'runtime_rebuild02',dest,ignore=shutil.ignore_patterns('__pycache__'))
    for name in ['search_mission.py','ardupilot_bridge/rescue_mission.py']:
        f=dest/name;s=f.read_text(encoding='utf-8').replace('flight_adapter_revision="rebuild02"','flight_adapter_revision="rebuild03"');f.write_text(s,encoding='utf-8')
    for name in ['search_worker.py','vla_worker.py']:
        f=dest/name;s=f.read_text(encoding='utf-8')
        s=s.replace('    policy=DroneVLA(args.checkpoint)','    policy=DroneVLA(args.checkpoint)\n    policy.policy.model.config.num_steps=5')
        s=s.replace('checkpoint_sha256=checkpoint_hash,inference_seed=20261024','checkpoint_sha256=checkpoint_hash,inference_seed=20261024,num_steps=5')
        s=s.replace('policy_kind="SmolVLA",checkpoint_sha256=checkpoint_hash)','policy_kind="SmolVLA",checkpoint_sha256=checkpoint_hash,num_steps=5)')
        ast.parse(s);f.write_text(s,encoding='utf-8')
    f=dest/'pipelined_camera.py';s=f.read_text(encoding='utf-8').replace("action_dt_s=response.get('action_dt_s'),perception=", "action_dt_s=response.get('action_dt_s'),num_steps=response.get('num_steps'),perception=");f.write_text(s,encoding='utf-8')
    for before,after in [('score_rebuild02.py','score_rebuild03.py'),('run_suite_rebuild02.py','run_suite_rebuild03.py'),('audit_rebuild02_execution.py','audit_rebuild03_execution.py'),('run_rebuild02_dev.py','run_rebuild03_dev.py')]:
        s=(W/'scripts'/before).read_text(encoding='utf-8').replace('rebuild02','rebuild03')
        ast.parse(s);(W/'scripts'/after).write_text(s,encoding='utf-8')
    base=read(W/'protocol/rebuild02_dev.json')
    plan=dict(base,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope='Same five preselected development conditions. Five flow steps were chosen by a preregistered offline speed/fidelity rule. Stop on first failure; no hidden retries.',
        hypothesis='Reduce actual image-to-result delay as well as increase update frequency.',
        changed=['Flow matching inference steps10 to5'],
        unchanged=['Weights,chunk32,renderer16samples','Endpoint tracker,PI and mission logic','All freshness and physical scoring thresholds','Battery/physics/WSL limits'],
        flow_steps=5,benchmark_sha256=sha(W/'reports/flow_steps_benchmark01.json'),
        runtime_sha256={p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file()},
        runner_sha256=sha(W/'scripts/run_suite_rebuild03.py'),score_sha256=sha(W/'scripts/score_rebuild03.py'),
        previous_batch='runs/rebuild02_dev/summary.json')
    with (W/'protocol/rebuild03_dev.json').open('x',encoding='utf-8') as f:json.dump(plan,f,indent=2)
    print(json.dumps(dict(flow_steps=5,chunk_size=32,weights_changed=False,cases=len(plan['cases']))))
if __name__=='__main__':main()
