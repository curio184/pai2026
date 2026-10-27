"""Independent optical revision, preserving validated dynamics and old builds."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parent
blend=ROOT/'assets/civic_realism/revision02.blend'
dest=ROOT/'assets/civic_realism/physics02';dest.mkdir(exist_ok=True)
for src in (ROOT/'assets/civic_world/physics').iterdir():shutil.copy2(src,dest/src.name)
sidecar=json.loads((dest/'rescue_scene.render.json').read_text())
sidecar.update(blend_sha256=hashlib.sha256(blend.read_bytes()).hexdigest(),blend_relative=blend.relative_to(ROOT).as_posix())
(dest/'rescue_scene.render.json').write_text(json.dumps(sidecar,indent=2))
manifest=json.loads((dest/'manifest.json').read_text());manifest['optical']=sidecar
manifest['human_contacts']='Original conservative primitive approximation; revised clothed mesh clearance must also be checked on actual new flight poses.'
manifest['policy_tested']=False
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2))
home=Path(r'\\wsl.localhost\Ubuntu-22.04\home\curio\physical_ai_ardupilot')
build=home/'realism_bridge_50g_v2';build.mkdir(exist_ok=False)
for name in ['libstampfly_plant.so','stampfly_payload.xml','build_result.json']:shutil.copy2(home/'civic_bridge_50g_v1'/name,build/name)
for src in dest.iterdir():shutil.copy2(src,build/src.name)
print(json.dumps(sidecar,indent=2))
