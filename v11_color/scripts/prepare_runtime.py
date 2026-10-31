import hashlib,json,difflib,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1];P=W.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=P/'tmp/rescue_search/plant_search.cpp';old=src.read_text(encoding='utf-8')
new=old.replace('#include <cmath>','#include <cmath>\n#include <cstdlib>\nstatic double initial(const char* key, double fallback) {\n    const char* v = std::getenv(key); return v ? std::stod(v) : fallback;\n}\n')
new=new.replace('c.noise.seed = 20261023;','c.noise.seed = static_cast<unsigned>(initial("V11_NOISE_SEED", 20261023));')
new=new.replace('const double heading = 1.5707963267948966;','const double heading = (90.0 + initial("V11_HEADING_OFFSET_DEG", 0.0)) * 3.14159265358979323846 / 180.0;\n    p->data()->qpos[0] += initial("V11_START_X_OFFSET", 0.0);\n    p->data()->qpos[1] += initial("V11_START_Y_OFFSET", 0.0);')
assert old!=new and 'V11_START_X_OFFSET' in new
(W/'runtime/plant_search_jitter.cpp').write_text(new,encoding='utf-8')
(W/'protocol/initial_pose_wrapper.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original/plant_search.cpp',tofile='plant_search_jitter.cpp')),encoding='utf-8')
snapshot=W/'runtime/ardupilot_bridge';snapshot.mkdir(exist_ok=True)
shutil.copy2(P/'ardupilot_bridge/rescue_mission.py',snapshot/'rescue_mission.py')
files={p.relative_to(W/'runtime').as_posix():sha(p) for p in (W/'runtime').rglob('*') if p.is_file() and '__pycache__' not in str(p)}
imports=['smolvla_policy.py','flight_progress.py','score_mission.py','civic_render_client.py','rescue_scene.py','civic_camera.py','vla_link.py','vla_worker.py','ardupilot_bridge/rescue_mission.py']
(W/'protocol/runtime_lock.json').write_text(json.dumps(dict(runtime=files,project_imports={n:sha(P/n) for n in imports},original_wrapper_sha256=sha(src),wrapper_changes='Only initial x/y/heading and sensor RNG seed set before integration; no dynamics, controller, gains, scoring changes.',source_root=str(P),script_sha256=sha(Path(__file__))),indent=2))
print('Runtime frozen',len(files))
