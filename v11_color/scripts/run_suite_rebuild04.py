"""Run rebuild04 flight cases: fixed 0.4 s simulated latency, VLA plan executed unchanged.

Derived from run_suite_rebuild03_final.py. Differences:
- runtime_rebuild04 (fixed_latency.py, no plan tracker), chunk origin 'capture', --latency 0.4
- wall-clock limits raised, because physics pauses while rendering/inference catch up
No automatic reruns. Every case directory is kept.
"""
import os,sys,json,time,hashlib,subprocess,datetime,argparse
from pathlib import Path
from bounded_wsl import bounded_command
W=Path(__file__).resolve().parents[1];P=W.parent
RT=W/'runtime_rebuild04'
PY=Path('<USER_HOME>/AppData/Local/Temp/physical_ai_drone_smolvla/venv/Scripts/python.exe')
BLENDER='C:/Program Files/Blender Foundation/Blender 3.1/blender.exe'
LINPY='<WSL_HOME>/physical_ai_drone_sitl/venv/bin/python'
OLD_BUILD='<WSL_HOME>/physical_ai_ardupilot/realism_bridge_50g_v2'
LATENCY_S=0.4
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def lp(p):
    p=Path(p).resolve();return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def ready(process,file,timeout):
    start=time.monotonic()
    while not file.exists():
        if process.poll() is not None:raise RuntimeError('Process exited before ready: '+str(file))
        if time.monotonic()-start>timeout:raise TimeoutError(str(file))
        time.sleep(.2)
    return json.loads(file.read_text())
def runtime_hashes():
    return {str(p.relative_to(RT)).replace('\\','/'):sha(p) for p in sorted(RT.rglob('*.py'))}

def run_case(case,checkpoint,out):
    out.mkdir(parents=True,exist_ok=False);worker=renderer=None;logs=[]
    search=case['kind']=='search'
    if search:
        scene=W/'scenes'/case['scene'] if case['scene'].startswith(('dev','heldout')) else P/'tmp/rescue_search/scenes'/case['scene']
        if case['scene']=='known_swapped':scene=P/'validation_v1_1/scenes/swapped'
    xml=scene/'physics/rescue_scene.xml' if search else Path('//wsl.localhost/Ubuntu-22.04'+OLD_BUILD)/'rescue_scene.xml'
    blend=scene/'scene.blend' if search else P/'assets/civic_realism/revision03.blend'
    build=W/'runtime/build' if search and case.get('jitter') else P/'tmp/rescue_search/build'
    checkpoint_hash=sha(checkpoint/'model.safetensors')
    manifest=dict(case=case,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checkpoint_sha256=checkpoint_hash,
        configuration='rebuild04',fixed_latency_s=LATENCY_S,chunk_origin='capture',plan_tracker_used=False,
        runtime_sha256=runtime_hashes(),physics_sha256=sha(xml),blend_sha256=sha(blend),runner_script_sha256=sha(Path(__file__)),
        automatic_retries=0,prompt_language='English',
        plant_sha256=sha(build/'libstampfly_plant.so') if search else sha(Path('//wsl.localhost/Ubuntu-22.04'+OLD_BUILD)/'libstampfly_plant.so'))
    write(out/'manifest.json',manifest)
    env=os.environ.copy();env.update(RESCUE_PROJECT_ROOT=str(P),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONUTF8='1')
    result=dict(id=case['id'],model=case.get('model','v1.1'),case=case,flight_started=False,success=False,record=str(out/'record'))
    print(json.dumps(dict(event='case_start',**case)),flush=True)
    started=time.monotonic()
    try:
        log=(out/'worker.log').open('w',encoding='utf-8');logs.append(log)
        worker=subprocess.Popen([str(PY),str(RT/('search_worker.py' if search else 'vla_worker.py')),'--checkpoint',str(checkpoint),'--sessions','1','--ready-file',str(out/'worker_ready.json'),'--connect-timeout','300'],env=env,stdout=log,stderr=subprocess.STDOUT)
        wr=ready(worker,out/'worker_ready.json',240);assert wr['checkpoint_sha256']==checkpoint_hash;assert wr['num_steps']==5
        log=(out/'renderer.log').open('w',encoding='utf-8');logs.append(log)
        renderer=subprocess.Popen([BLENDER,'--factory-startup','--background','--python',str(P/'civic_render_client.py'),'--','1',str(out/'renderer_ready.json'),str(blend)],env=env,stdout=log,stderr=subprocess.STDOUT)
        rr=ready(renderer,out/'renderer_ready.json',120);assert rr['blend_sha256']==manifest['blend_sha256']
        extras=[]
        if case.get('jitter'):
            x,y,h=case['initial_offset'];extras=[f'V11_START_X_OFFSET={x}',f'V11_START_Y_OFFSET={y}',f'V11_HEADING_OFFSET_DEG={h}',f"V11_NOISE_SEED={case['seed']}"]
        command=['wsl','-d','Ubuntu-22.04','--exec','env','RESCUE_PROJECT_ROOT='+lp(P),*extras,LINPY,lp(RT/('search_mission.py' if search else 'ardupilot_bridge/rescue_mission.py')),
            '--build',lp(build) if search else OLD_BUILD,'--scene',lp(xml) if search else OLD_BUILD+'/rescue_scene.xml','--output',lp(out/'record'),
            '--chunk-origin','capture','--latency',str(LATENCY_S),'--wall-limit','1500']
        if search:command+=['--instruction','青い服の人を探して' if case['color']=='blue' else '赤い服の人を探して']
        else:command+=['--profile',case['profile']]
        command=bounded_command(command,out)
        write(out/'command.json',command);result['flight_started']=True
        with (out/'runner.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
        result['runner_exit']=run.returncode
        if run.returncode:raise RuntimeError('Flight runner returned '+str(run.returncode))
        scorer=W/'scripts/score_rebuild04.py'
        with (out/'scoring.log').open('w',encoding='utf-8') as log:
            scored=subprocess.run([str(PY),str(scorer),str(out/'record'),'--scene',str(xml)]+(['--search'] if search else []),env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
        if scored.returncode:raise RuntimeError('Scorer failed; see scoring.log')
        verdict=json.loads((out/'record'/('search_score.json' if search else 'physical_score.json')).read_text())
        result.update(success=verdict['success'],checks=verdict.get('checks'),checkpoint_sha256=checkpoint_hash)
        if search and case.get('jitter'):
            first=json.loads((out/'record/trace.jsonl').open().readline())
            write(out/'initial_truth_audit.json',dict(first_trace_time=first['t'],qpos=first['truth'][19:26],planned_offset=case['initial_offset'],teacher_only=True))
    except BaseException as e:result['error']=repr(e)
    finally:
        for proc in [renderer,worker]:
            if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=30)
        for log in logs:log.close()
    result['wall_s']=time.monotonic()-started
    write(out/'outcome.json',result);print(json.dumps(result,ensure_ascii=False),flush=True);return result

def main():
    a=argparse.ArgumentParser();a.add_argument('protocol');a.add_argument('--group',required=True)
    args=a.parse_args()
    protocol=json.loads(Path(args.protocol).read_text(encoding='utf-8'))
    if protocol.get('runtime_sha256'):
        assert runtime_hashes()==protocol['runtime_sha256'],'runtime changed after registration'
    checkpoint=W/'models'/protocol['candidate']/'final'
    assert sha(checkpoint/'model.safetensors')==protocol['checkpoint_sha256']
    root=W/'runs'/args.group;root.mkdir(parents=True,exist_ok=False)
    write(root/'suite_plan.json',protocol)
    outcomes=[]
    for case in protocol['cases']:
        outcomes.append(run_case(case,checkpoint,root/case['id']))
        write(root/'summary.json',dict(cases=outcomes,completed=len(outcomes),planned=len(protocol['cases'])))
    print(json.dumps(dict(event='suite_done',group=args.group,success=sum(o['success'] for o in outcomes),planned=len(outcomes))),flush=True)
if __name__=='__main__':main()
