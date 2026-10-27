"""Local-only GPU/WSL integration. Each run is immutable; every attempt retained."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT'])
def lp(p):
    p=Path(p).resolve();return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def wait_ready(process,file,timeout):
    start=time.monotonic()
    while not file.exists():
        if process.poll() is not None:raise RuntimeError(f'Process failed: {process.returncode}: {file}')
        if time.monotonic()-start>timeout:raise TimeoutError(str(file))
        time.sleep(.2)
    return json.loads(file.read_text())
def main(args):
    out=HERE/'runs'/args.name;out.mkdir(parents=True,exist_ok=False)
    checkpoint=args.checkpoint or ROOT/'outputs/smolvla_training_realism_precision_02/final'
    cases=[dict(condition=c,profile=args.profile) for c in args.conditions]
    sources=['search_worker.py','search_mission.py','search_link.py','confirmation.py','perception.py','plant_search.cpp','run_search.py']
    snapshot=out/'source_snapshot';snapshot.mkdir()
    for n in sources:shutil.copy2(HERE/n,snapshot/n)
    manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),cases=cases,checkpoint_sha256=sha(checkpoint/'model.safetensors'),
                  source_sha256={n:sha(HERE/n) for n in sources},scene_conditions=json.loads((HERE/'scene_conditions.json').read_text()),
                  initial_pose=json.loads((HERE/'build/initial_pose_check.json').read_text()),
                  scope='development' if args.development else 'frozen evaluation',automatic_retries=0,
                  ground_truth_navigation=False,external_communication=False,
                  upper_command='青い服の人を探して' if args.profile=='blue' else '赤い服の人を探して')
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    workerlog=(out/'worker.log').open('w',encoding='utf8');renderer=None;rendererlog=None
    env=os.environ.copy();env.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONUTF8='1')
    worker=subprocess.Popen([sys.executable,str(HERE/'search_worker.py'),'--checkpoint',str(checkpoint),'--sessions',str(len(cases)),
                             '--ready-file',str(out/'worker_ready.json'),'--connect-timeout','300'],env=env,stdout=workerlog,stderr=subprocess.STDOUT)
    try:
        ready=wait_ready(worker,out/'worker_ready.json',180)
        assert ready['checkpoint_sha256']==manifest['checkpoint_sha256']
        records=[]
        for case in cases:
            cond=case['condition'];name=cond+'_'+case['profile'];scene=HERE/'scenes'/cond
            rendererlog=(out/(name+'_render.log')).open('w',encoding='utf8')
            renderer=subprocess.Popen([r'C:\Program Files\Blender Foundation\Blender 3.1\blender.exe','--factory-startup','--background','--python',str(ROOT/'civic_render_client.py'),'--','1',str(out/(name+'_render_ready.json')),str(scene/'scene.blend')],stdout=rendererlog,stderr=subprocess.STDOUT)
            render_ready=wait_ready(renderer,out/(name+'_render_ready.json'),90)
            assert render_ready['blend_sha256']==sha(scene/'scene.blend')
            command=['wsl','-d','Ubuntu-22.04','--exec','env','RESCUE_PROJECT_ROOT='+lp(ROOT),
                     '/home/USER/physical_ai_drone_sitl/venv/bin/python',lp(HERE/'search_mission.py'),
                     '--build',lp(HERE/'build'),'--scene',lp(scene/'physics/rescue_scene.xml'),
                     '--output',lp(out/name),'--instruction',manifest['upper_command'],'--chunk-origin','split']
            print(json.dumps(dict(event='flight_start',**case)),flush=True)
            with (out/(name+'_runner.log')).open('w',encoding='utf8') as log:
                result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=340)
            records.append(dict(**case,runner_exit=result.returncode))
            (out/'progress.json').write_text(json.dumps(records,indent=2))
            print(json.dumps(records[-1]),flush=True)
            if renderer.poll() is None:renderer.terminate()
            renderer.wait(timeout=15);renderer=None
            rendererlog.close();rendererlog=None
            if result.returncode:raise RuntimeError('Flight runner failed; inspect preserved record')
        worker.wait(timeout=30)
        (out/'finished.json').write_text(json.dumps(dict(records=records,worker_exit=worker.returncode),indent=2))
    except BaseException as e:
        (out/'failure.json').write_text(json.dumps(dict(error=repr(e)),indent=2));raise
    finally:
        for p in [renderer,worker]:
            if p is not None and p.poll() is None:
                p.terminate();p.wait(timeout=15)
        if rendererlog:rendererlog.close()
        workerlog.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--name',required=True)
    p.add_argument('--conditions',nargs='+',default=['clear'],choices=['clear','fog_light','fog_dense','dust'])
    p.add_argument('--profile',default='blue',choices=['blue','red'])
    p.add_argument('--checkpoint',type=Path);p.add_argument('--development',action='store_true')
    main(p.parse_args())
