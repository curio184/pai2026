import ctypes
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import mujoco
import numpy as np

here=Path(__file__).resolve().parent
out=here/'build'
out.mkdir(exist_ok=False)
source=Path.home()/'physical_ai_stampfly/stampfly_ecosystem'
old=Path.home()/'physical_ai_ardupilot/realism_bridge_50g_v2'
for name in ['build_result.json','stampfly_payload.xml']:
    shutil.copy2(old/name,out/name)
mj=Path(mujoco.__file__).parent
sils=source/'simulator/sils'
vehicle=source/'firmware/vehicle/components'
command=['g++','-shared','-fPIC','-O2','-std=c++17',str(here/'plant_search.cpp'),str(sils/'plant/plant.cpp')]
for inc in [sils/'plant',sils/'frames',vehicle/'sf_math/include',vehicle/'sf_core/include',mj/'include']:
    command+=['-I',str(inc)]
command += [str(next(mj.glob('libmujoco.so.*'))),'-Wl,-rpath,'+str(mj),'-o',str(out/'libstampfly_plant.so')]
subprocess.run(command,check=True)
lib=ctypes.CDLL(str(out/'libstampfly_plant.so'))
lib.sf_create.argtypes=[ctypes.c_char_p,ctypes.c_float];lib.sf_create.restype=ctypes.c_void_p
lib.sf_step.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_double),ctypes.c_double,ctypes.POINTER(ctypes.c_double)]
lib.sf_destroy.argtypes=[ctypes.c_void_p]
ptr=lib.sf_create(str(here/'scenes/clear/physics/rescue_scene.xml').encode(),.05)
assert ptr
state=np.zeros(32);duty=np.zeros(4)
lib.sf_step(ptr,duty.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),0,state.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
lib.sf_destroy(ptr)
assert np.allclose(state[22:26],[2**-.5,0,0,2**-.5],atol=1e-6),state
report=dict(initial_state=state.tolist(),initial_condition_only=True,
            original_plant_modified=False,wrapper_sha256=hashlib.sha256((here/'plant_search.cpp').read_bytes()).hexdigest(),
            library_sha256=hashlib.sha256((out/'libstampfly_plant.so').read_bytes()).hexdigest())
(out/'initial_pose_check.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
