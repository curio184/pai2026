"""Untrained teacher proposal, not a runtime controller or registered experiment.

The base teacher remains responsible for navigation, altitude, yaw and requests.
Only takeoff/turn/hover horizontal labels gain a captured-own-state correction.
The correction is held over the chunk because the execution adapter uses delayed
capture-time linear actions. A new observation produces a new plan. No physical
success, causal attribution or approval of a new final evaluation is implied.
"""
import numpy as np

def make_teacher(baseline,scale,coefficient=.8):
    def teacher_chunk(task,qpos,own,targets,steps=32):
        chunk=baseline(task,qpos,own,targets,steps).copy()
        if task in (2,4,5,6) and own[8]>.5:
            braking=-coefficient*np.asarray(own[:2],dtype=float)
            norm=np.linalg.norm(braking)
            if norm>.2:braking*=.2/norm
            chunk[:,:2]=braking/np.asarray(scale[:2])
        return chunk
    return teacher_chunk

if __name__=='__main__':
    import hashlib,json,math,sys
    from pathlib import Path
    w=Path(__file__).resolve().parents[1];sys.path.insert(0,str(w.parent))
    from make_revision_data import rotation,SCALE
    baseline_path=w/'data/dataset03/teacher_source.py'
    namespace=dict(np=np,math=math,rotation=rotation,SCALE=SCALE)
    exec(compile(baseline_path.read_text(encoding='utf-8'),str(baseline_path),'exec'),namespace)
    baseline=namespace['teacher_chunk'];proposed=make_teacher(baseline,SCALE)
    targets=dict(blue=np.array([3.,.8,0]),red=np.array([3.,-.8,0]))
    q=np.array([1.,0,1.,1,0,0,0]);checked=0
    for velocity in [[0,0],[.1,0],[-.1,0],[0,.1],[0,-.1],[.2,.2]]:
        for armed in [0.,1.]:
            for task in range(7):
                state=np.array([*velocity,0.,1.,0.,0.,.7,0.,armed])
                old=baseline(task,q,state,targets);new=proposed(task,q,state,targets)
                assert np.array_equal(new[:,2:],old[:,2:])
                if task in [0,1,3] or not armed:assert np.array_equal(new,old)
                elif np.linalg.norm(velocity)>0:
                    assert np.all((new[:,:2]*SCALE[:2])@np.array(velocity)<0)
                else:assert np.all(new[:,:2]==0)
                assert np.max(np.linalg.norm(new[:,:2]*SCALE[:2],axis=1))<=.200001
                checked+=1
    result=dict(proposal=True,synthetic_cases=checked,passed=True,
        unchanged=['navigation','landing','unarmed actions','vertical velocity','yaw','takeoff and landing requests'],
        note='Algebraic teacher checks only, not model inference or flight evaluation.',
        baseline_sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (w/'reports/teacher_braking_proposal_check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
