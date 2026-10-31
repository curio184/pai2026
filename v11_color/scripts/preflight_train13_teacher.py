"""Check yaw direction, limits, and unchanged primitives before training."""
import datetime,hashlib,json,math,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(W.parent))
from make_revision_data import rotation,SCALE
from teacher_flight12 import teacher_chunk as previous
from teacher_flight13 import teacher_chunk

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=W/'protocol/train13_english.json'; assert plan.exists()
    out=W/'reports/train13_teacher_preflight_audit.json'; assert not out.exists()
    checks=[]
    # Synthetic teacher-only geometry, not a simulation flight or a policy input.
    targets={'blue':np.array([2.,.7,0.]),'red':np.array([2.,-.7,0.])}
    q=np.array([0.,0.,1.,1.,0.,0.,0.]); own=np.array([.03,-.02,0.,1.,0.,0.,0.,0.,1.])
    for task in [0,1]:
        chunk=teacher_chunk(task,q,own,targets,rotation,SCALE)*SCALE
        expected_sign=-1 if task==0 else 1
        assert np.sign(chunk[0,3])==expected_sign
        assert np.max(np.abs(chunk[:,3]))<=.250001
        assert np.max(np.linalg.norm(chunk[:,:2],axis=1))<=.200001
        original=previous(task,q,own,targets,rotation,SCALE)*SCALE
        assert np.array_equal(chunk[:,[2,4,5]],original[:,[2,4,5]])
        checks.append(dict(task=task,first_yaw=float(chunk[0,3]),expected_sign=expected_sign))
    centered={'blue':np.array([2.,0.,0.]),'red':np.array([2.,0.,0.])}
    stationary=own.copy(); stationary[:2]=0.
    assert np.count_nonzero(teacher_chunk(0,q,stationary,centered,rotation,SCALE)[:,3])==0
    primitive_checks=0
    for task in range(2,7):
        for altitude in [.1,.9,1.1]:
            for armed in [0.,1.]:
                s=own.copy();s[3]=altitude;s[8]=armed;s[6]=.5;s[7]=.1
                assert np.array_equal(teacher_chunk(task,q,s,targets,rotation,SCALE),previous(task,q,s,targets,rotation,SCALE))
                primitive_checks+=1
    with np.load(W/'data/dataset13_en/audited_samples.npz') as d:
        tasks=d['task'];actions=d['action'];states=d['state']
    with np.load(W/'data/dataset12_en/audited_samples.npz') as d:old=d['action']
    assert np.array_equal(actions[tasks>=2],old[tasks>=2])
    assert np.array_equal(actions[:,:,[2,4,5]],old[:,:,[2,4,5]])
    airborne=(tasks<2)&(states[:,8]>.5)&(states[:,3]>.8)
    assert np.count_nonzero(actions[airborne,:,3])>0
    result=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,
        plan_sha256=sha(plan),teacher_sha256=sha(W/'scripts/teacher_flight13.py'),
        dataset_audit_sha256=sha(W/'data/dataset13_en/audit.json'),yaw_sign_checks=checks,
        primitive_examples_checked=primitive_checks,all_materialized_primitive_labels_identical=True,
        all_vertical_and_request_labels_identical=True,centering_zero_when_centered=True,
        optimization_steps=0,policy_inferences=0,flight_trials=0,
        scope='Teacher geometry/unit checks and full materialized-label invariants only; not evidence of policy success.')
    out.write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
if __name__=='__main__':main()
