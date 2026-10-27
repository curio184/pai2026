"""Read-only independent frustum check of recorded initial search images."""
import json, math, os
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT'])/'tmp/rescue_search'
def read(p): return json.loads(p.read_text(encoding='utf8'))
rows=[]
for name in ['clear','fog_light','fog_dense','dust']:
    d=ROOT/'runs/eval03'/f'{name}_blue'
    start=read(d/'search_start_observation.json')
    trace=[json.loads(s) for s in (d/'trace.jsonl').read_text().splitlines()]
    state=min(trace,key=lambda r:abs(r['t']-start['t']))
    q=np.array(state['truth'][19:26]); w=q[3]; v=q[4:]
    def rotate(p): return p+2*w*np.cross(v,p)+2*np.cross(v,np.cross(v,p))
    forward=rotate(np.array([1.,0.,0.])); left=rotate(np.array([0.,1.,0.]))
    camera=q[:3]+rotate(np.array([.014,0,.025]))
    person=ET.parse(ROOT/'scenes'/name/'physics/rescue_scene.xml').getroot().find("worldbody/body[@name='blue_person']")
    target=np.fromstring(person.get('pos'),sep=' ')
    rays=[target+np.array([x,y,z])-camera for x in [-.35,.35] for y in [-.35,.35] for z in [0,1.9]]
    half=math.atan(math.tan(math.radians(32))*4/3)
    angles=[math.degrees(math.atan2(np.dot(r,left),np.dot(r,forward))) for r in rays]
    # Signed plane test on the box avoids angle wrapping at +/-180 degrees.
    plane_left=[float(np.dot(r,left)-np.dot(r,forward)*math.tan(half)) for r in rays]
    plane_right=[float(-np.dot(r,left)-np.dot(r,forward)*math.tan(half)) for r in rays]
    outside=min(plane_left)>0 or min(plane_right)>0 or max(float(np.dot(r,forward)) for r in rays)<0
    assert outside
    rows.append(dict(condition=name,angles_degrees=[min(angles),max(angles)],horizontal_half_fov_degrees=math.degrees(half),outside=bool(outside),nearest_trace_time_error_s=abs(state['t']-start['t'])))
(ROOT/'reviews/independent_geometry_audit.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
print(json.dumps(rows,indent=2))
