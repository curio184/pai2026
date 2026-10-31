"""Bounded import/library-load check only; no physics steps, model, or flight."""
import hashlib,json,subprocess
from pathlib import Path
from bounded_wsl import bounded_command
W=Path(__file__).resolve().parents[1];out=W/'reports/wsl_bounded_smoke';out.mkdir(exist_ok=False)
payload="import os,json,ctypes,numpy;ctypes.CDLL('<PROJECT_ROOT>/v11_color/runtime/build/libstampfly_plant.so');print(json.dumps(dict(uid=os.getuid(),home=os.environ['HOME'],affinity=sorted(os.sched_getaffinity(0)),numpy=numpy.__version__,plant_loaded=True,physics_steps=0)))"
base=['wsl','-d','Ubuntu-22.04','--exec','env','RESCUE_PROJECT_ROOT=<PROJECT_ROOT>','<WSL_HOME>/physical_ai_drone_sitl/venv/bin/python','-c',payload]
command=bounded_command(base,out)
result=subprocess.run(command,capture_output=True,timeout=30)
report=dict(command=command,exit=result.returncode,stdout=result.stdout.decode('utf8',errors='replace'),stderr=result.stderr.decode('utf8',errors='replace'),flight=False,model_inference=False,physics_steps=0)
(out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report));assert result.returncode==0
usage=json.loads((out/'resource_usage.json').read_text())
assert 'oom_kill 0' in usage['measurements']['memory.events']
print(json.dumps(usage))
