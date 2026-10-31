"""Algebraic check against the saved legacy teacher; no policy or flight."""
import hashlib,importlib.util,json,math
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p,name):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def rotation(q):
    w,x,y,z=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def main():
    scale=np.array([.2,.2,.3,.35,1,1]);ns=dict(np=np,math=math,rotation=rotation,SCALE=scale)
    teacher=P/'outputs/vla_data_realism_precision_02/teacher_source.py';exec(teacher.read_text(encoding='utf-8'),ns)
    decoder=load(W/'runtime_rebuild03_v10ref/plan_endpoint.py','legacy_semantic_decoder')
    rows=[]
    for goal,yaw,v in [([.3,.2],0,[0,0]),([.15,-.1],.2,[.04,-.02]),([.05,.02],0,[0,0]),([.5,-.2],-.3,[-.03,.05])]:
        q=np.array([0,0,1,math.cos(yaw/2),0,0,math.sin(yaw/2)])
        own=np.array([*v,0,1,0,0,yaw,0,1.])
        chunk=ns['teacher_chunk'](0,q,own,dict(blue=np.array([goal[0]+.9,goal[1],0]))) * scale
        endpoint,details=decoder.decode_plan_endpoint(chunk,own)
        expected=rotation(q[3:])[:2,:2].T@goal;error=float(np.linalg.norm(endpoint-expected))
        assert error<=.045,(goal,error)
        rows.append(dict(goal=goal,yaw=yaw,own_velocity=v,error_m=error))
    out=W/'reports/rebuild03_v10_decoder_preflight.json';out.write_text(json.dumps(dict(passed=True,teacher_sha256=sha(teacher),cases=rows,scope='Synthetic teacher algebra only; no real closed-loop success claim.',flights=0,policy_inferences=0),indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,max_error_m=max(r['error_m'] for r in rows))))
if __name__=='__main__':main()
