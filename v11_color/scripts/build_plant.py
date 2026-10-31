"""WSL build; test initial conditions with dt=0, no policy or evaluation flight."""
import ctypes,hashlib,json,shutil,subprocess,os
from pathlib import Path
import mujoco,numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent;out=W/'runtime/build';out.mkdir(exist_ok=False)
source=Path.home()/'physical_ai_stampfly/stampfly_ecosystem';old=Path.home()/'physical_ai_ardupilot/realism_bridge_50g_v2'
for name in ['build_result.json','stampfly_payload.xml']:shutil.copy2(old/name,out/name)
mj=Path(mujoco.__file__).parent;sils=source/'simulator/sils';vehicle=source/'firmware/vehicle/components'
cmd=['g++','-shared','-fPIC','-O2','-std=c++17',str(W/'runtime/plant_search_jitter.cpp'),str(sils/'plant/plant.cpp')]
for inc in [sils/'plant',sils/'frames',vehicle/'sf_math/include',vehicle/'sf_core/include',mj/'include']:cmd+=['-I',str(inc)]
cmd += [str(next(mj.glob('libmujoco.so.*'))),'-Wl,-rpath,'+str(mj),'-o',str(out/'libstampfly_plant.so')]
subprocess.run(cmd,check=True)
lib=ctypes.CDLL(str(out/'libstampfly_plant.so'));lib.sf_create.argtypes=[ctypes.c_char_p,ctypes.c_float];lib.sf_create.restype=ctypes.c_void_p
lib.sf_step.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_double),ctypes.c_double,ctypes.POINTER(ctypes.c_double)];lib.sf_destroy.argtypes=[ctypes.c_void_p]
states=[]
for x,y,h in [(0,0,0),(.05,-.05,5),(-.05,.05,-5)]:
    os.environ.update(V11_START_X_OFFSET=str(x),V11_START_Y_OFFSET=str(y),V11_HEADING_OFFSET_DEG=str(h))
    ptr=lib.sf_create(str(P/'tmp/rescue_search/scenes/clear/physics/rescue_scene.xml').encode(),.05);assert ptr
    s=np.zeros(32);d=np.zeros(4);lib.sf_step(ptr,d.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),0,s.ctypes.data_as(ctypes.POINTER(ctypes.c_double)));lib.sf_destroy(ptr)
    assert np.allclose(s[19:21],[x,y],atol=1e-6),s.tolist()
    assert np.allclose(s[22:26],[np.cos(np.deg2rad(90+h)/2),0,0,np.sin(np.deg2rad(90+h)/2)],atol=1e-6)
    states.append(dict(offset=[x,y,h],initial_state=s.tolist()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(out/'initial_pose_check.json').write_text(json.dumps(dict(checks=states,zero_time_only=True,original_plant_modified=False,original_plant_source_sha256=sha(sils/'plant/plant.cpp'),wrapper_sha256=sha(W/'runtime/plant_search_jitter.cpp'),library_sha256=sha(out/'libstampfly_plant.so'),command=cmd),indent=2))
print('Initial condition checks passed',len(states))
