"""Post-flight dependency inventory; not represented as a pre-flight lock."""
import hashlib
import importlib.metadata as md
import json
import os
from pathlib import Path
import subprocess
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);HERE=Path(__file__).resolve().parent
files=['smolvla_policy.py','rescue_scene.py','civic_camera.py','civic_render_client.py','flight_progress.py','vla_link.py','score_mission.py']
report=dict(timing='Collected after eval03; supporting files unchanged during this goal',
            root_sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in files},
            versions={n:md.version(n) for n in ['torch','torchvision','transformers','lerobot','opencv-python-headless','pillow','numpy']})
commands={
 'stampfly_commit':['git','-C','/home/USER/physical_ai_stampfly/stampfly_ecosystem','rev-parse','HEAD'],
 'ardupilot_commit':['git','-C','/home/USER/physical_ai_ardupilot/ardupilot','rev-parse','HEAD'],
 'stampfly_status':['git','-C','/home/USER/physical_ai_stampfly/stampfly_ecosystem','status','--porcelain'],
 'ardupilot_status':['git','-C','/home/USER/physical_ai_ardupilot/ardupilot','status','--porcelain'],
}
for key,command in commands.items():
    report[key]=subprocess.check_output(['wsl','-d','Ubuntu-22.04','--exec',*command],text=True,encoding='utf8').strip()
assert report['stampfly_commit']=='9467f1a156326b95a01383e11c44dd665a55b536'
assert report['ardupilot_commit']=='38687117133582049734ebd39f8a7af6f487716a'
dest=HERE/'runs/eval03/postflight_dependency_manifest.json'
dest.write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
