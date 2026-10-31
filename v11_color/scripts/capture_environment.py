import importlib.metadata as md,json,platform,subprocess,sys,hashlib,datetime
from pathlib import Path
W=Path(__file__).resolve().parents[1]
packages=['torch','torchvision','transformers','lerobot','numpy','Pillow','safetensors','huggingface-hub']
versions={}
for name in packages:
    try:versions[name]=md.version(name)
    except md.PackageNotFoundError:versions[name]='not installed'
gpu=subprocess.run(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout.strip()
linux_code="import json,platform,importlib.metadata as m; print(json.dumps(dict(python=platform.python_version(),packages={n:m.version(n) for n in ['mujoco','numpy','pymavlink']})))"
linux=subprocess.run(['wsl','-d','Ubuntu-22.04','--exec','<WSL_HOME>/physical_ai_drone_sitl/venv/bin/python','-c',linux_code],capture_output=True,text=True,check=True)
ap=subprocess.run(['wsl','-d','Ubuntu-22.04','--exec','git','-C','<WSL_HOME>/physical_ai_ardupilot/ardupilot','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
diff=subprocess.run(['wsl','-d','Ubuntu-22.04','--exec','git','-C','<WSL_HOME>/physical_ai_ardupilot/ardupilot','diff','--stat'],capture_output=True,text=True,check=True).stdout.strip()
record=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=platform.python_version(),os=platform.system(),packages=versions,gpu=gpu,linux_physics=json.loads(linux.stdout),ardupilot_commit=ap,ardupilot_tracked_diff=diff,training_script_sha256=hashlib.sha256((W/'scripts/train.py').read_bytes()).hexdigest())
dest=W/'protocol/environment.json'
with dest.open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
print(json.dumps(record))
