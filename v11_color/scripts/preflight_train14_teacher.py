"""Check teacher signs, anticipatory braking, and preserved target channels."""
import datetime,hashlib,json,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W.parent))
from make_revision_data import rotation,SCALE
from teacher_flight13 import teacher_chunk as previous
from teacher_flight14 import teacher_chunk,BRAKING_COEFFICIENT,NAVIGATION_LOOKAHEAD_S
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=W/'protocol/train14_english.json';assert plan.exists()
    out=W/'reports/train14_teacher_preflight_audit.json';assert not out.exists()
    q=np.array([0.,0.,1.,1.,0.,0.,0.]);own=np.array([0.,0.,0.,1.,0.,0.,0.,0.,1.])
    targets={'blue':np.array([2.,.7,0.]),'red':np.array([2.,-.7,0.])};checks=[]
    for task,expected in [(0,-1),(1,1)]:
        a=teacher_chunk(task,q,own,targets,rotation,SCALE)*SCALE
        assert np.sign(a[0,3])==expected
        assert np.max(np.abs(a[:,3]))<=.250001 and np.max(np.linalg.norm(a[:,:2],axis=1))<=.200001
        checks.append(dict(task=task,first_yaw=float(a[0,3]),expected_sign=expected))
    centered={c:np.array([2.,0.,0.]) for c in ['blue','red']}
    assert np.count_nonzero(teacher_chunk(0,q,own,centered,rotation,SCALE)[:,3])==0
    s=own.copy();s[7]=.2
    yaw=float((teacher_chunk(0,q,s,centered,rotation,SCALE)*SCALE)[0,3])
    assert abs(yaw+.16)<1e-6,'Positive clockwise rate must be countered at centered bearing'
    s=own.copy();s[1]=.2
    lateral_yaw=float((teacher_chunk(0,q,s,centered,rotation,SCALE)*SCALE)[0,3])
    assert lateral_yaw>0,'Leftward translation predicts a rightward relative target bearing'
    primitive=0
    for task in range(2,7):
        for altitude in [.1,.9,1.1]:
            for armed in [0.,1.]:
                s=own.copy();s[:2]=[.03,-.02];s[3]=altitude;s[8]=armed;s[6]=.5;s[7]=.1
                old=previous(task,q,s,targets,rotation,SCALE);new=teacher_chunk(task,q,s,targets,rotation,SCALE)
                assert np.array_equal(new[:,2:],old[:,2:])
                if task==3:assert np.array_equal(new,old)
                else:
                    expected=np.zeros(2) if armed<.5 or (task==2 and altitude<.25) else -1.6*s[:2]
                    assert np.allclose(new[:,:2]*SCALE[:2],expected,atol=1e-7)
                primitive+=1
    with np.load(W/'data/dataset14_en/audited_samples.npz') as d:tasks=d['task'];actions=d['action'];states=d['state']
    with np.load(W/'data/dataset13_en/audited_samples.npz') as d:old=d['action']
    assert np.array_equal(actions[tasks==3],old[tasks==3])
    assert np.array_equal(actions[tasks>=2,:,3],old[tasks>=2,:,3])
    assert np.array_equal(actions[:,:,[2,4,5]],old[:,:,[2,4,5]])
    hold=np.isin(tasks,[2,4,5,6]);s=states[hold];t=tasks[hold]
    b=-1.6*s[:,:2].astype(float);b[(s[:,8]<.5)|((t==2)&(s[:,3]<.25))]=0
    b*=np.minimum(1.,.2/np.maximum(np.linalg.norm(b,axis=1,keepdims=True),1e-12))
    assert np.allclose(actions[hold,:,:2]*SCALE[:2],b[:,None,:],rtol=0,atol=1e-6)
    result=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,
        plan_sha256=sha(plan),teacher_sha256=sha(W/'scripts/teacher_flight14.py'),dataset_audit_sha256=sha(W/'data/dataset14_en/audit.json'),
        yaw_sign_checks=checks,centered_clockwise_rate_point2_produces_yaw=yaw,lateral_prediction_yaw=lateral_yaw,
        braking_coefficient=BRAKING_COEFFICIENT,navigation_lookahead_s=NAVIGATION_LOOKAHEAD_S,
        primitive_examples_checked=primitive,landing_targets_identical=True,primitive_yaw_identical=True,
        vertical_and_requests_identical=True,materialized_stationary_targets_checked=True,
        optimization_steps=0,policy_inferences=0,flight_trials=0,
        scope='Teacher geometry/sign checks and materialized-label invariants only, not evidence of learned flight success.')
    out.write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
if __name__=='__main__':main()
