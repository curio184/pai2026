"""Freeze pipeline correction separately; do not modify prior runtime or results."""
import ast,datetime,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    dest=W/'runtime_rebuild02';assert not dest.exists()
    shutil.copytree(W/'runtime_rebuild01',dest,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(W/'scripts/pipelined_camera.py',dest/'pipelined_camera.py')
    for name in ['search_mission.py','ardupilot_bridge/rescue_mission.py']:
        f=dest/name;s=f.read_text(encoding='utf-8')
        s=s.replace('from search_link import CameraLink,ActionGate','from search_link import ActionGate\nfrom pipelined_camera import CameraLink')
        s=s.replace('from vla_link import CameraLink,ActionGate','from vla_link import ActionGate\nfrom pipelined_camera import CameraLink')
        s=s.replace('flight_adapter_revision="rebuild01"','flight_adapter_revision="rebuild02"')
        if name=='search_mission.py':
            line='                if phase in (args.profile,"report") and visual.last_seen is not None and t-visual.last_seen>3.0:'
            assert line in s
            s=s.replace(line,'                model_packet=link.read()\n                confirmed=visual.update(model_packet,t)\n'+line)
            block='                link.submit(t,state[19:26],state[26:32],own_state,prompt)\n                model_packet=link.read()\n                confirmed=visual.update(model_packet,t)'
            assert block in s;s=s.replace(block,'                link.submit(t,state[19:26],state[26:32],own_state,prompt)')
        ast.parse(s);f.write_text(s,encoding='utf-8')
    for before,after in [('score_rebuild01.py','score_rebuild02.py'),('run_suite_rebuild01.py','run_suite_rebuild02.py'),('audit_rebuild01_execution.py','audit_rebuild02_execution.py')]:
        s=(W/'scripts'/before).read_text(encoding='utf-8').replace('rebuild01','rebuild02')
        ast.parse(s);(W/'scripts'/after).write_text(s,encoding='utf-8')
    prior=read(W/'protocol/navfocus_receipt.json');base=read(W/'protocol/rebuild01_dev.json')
    ids=['NFH06','NFH07','NFH08','search_fog_dense_blue','primitive_blue']
    cases=[next(c for c in prior['cases'] if c['id']==name and c['model']=='v1.1') for name in ids]
    for c in cases:c['group']='development_pipeline_diagnostic'
    plan=dict(base,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=cases,
        scope='Development pipeline diagnostic. Preselected observed failures plus dense fog and primitive approach. Stop on first failure for analysis; keep unrun cases explicitly unrun.',
        hypothesis='Serial rendering and inference make image age exceed unchanged freshness gates. Latest-frame pipelining removes serial waiting, and perception updates precede lost-target decisions.',
        changed=['Latest-frame single-slot rendering/inference pipeline','Read newest perception before deciding target lost'],
        unchanged=['Model, renderer quality and images','All physical score thresholds','Stale2.5s/watchdog8s/discovery3frames/lastseen3s/hits5s','Endpoint tracker and PI gains','Battery and physics','WSL4CPU/8GiB'],
        stop_on_failure=True,
        runtime_sha256={p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file()},
        runner_sha256=sha(W/'scripts/run_suite_rebuild02.py'),score_sha256=sha(W/'scripts/score_rebuild02.py'),
        previous_batch='runs/rebuild01_expanded/batch_closed.json')
    with (W/'protocol/rebuild02_dev.json').open('x',encoding='utf-8') as f:json.dump(plan,f,indent=2)
    print(json.dumps(dict(cases=ids,pipeline=True,model_changed=False)))
if __name__=='__main__':main()
