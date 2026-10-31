"""Verify label preservation and braking geometry before training, no flight."""
import datetime,hashlib,json,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W.parent))
from make_revision_data import rotation,SCALE
from teacher_flight14 import teacher_chunk as previous
from teacher_flight15 import teacher_chunk,BRAKING_COEFFICIENT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=W/'protocol/train15_english.json';assert plan.exists()
out=W/'reports/train15_teacher_preflight_audit.json';assert not out.exists()
q=np.array([0.,0.,1.,1.,0.,0.,0.]);own=np.array([.03,-.02,0.,1.,0.,0.,.5,.1,1.])
targets={'blue':np.array([2.,.7,0.]),'red':np.array([2.,-.7,0.])};checks=0
for task in range(7):
    for altitude in [.1,.9,1.1]:
        for armed in [0.,1.]:
            s=own.copy();s[3]=altitude;s[8]=armed
            old=previous(task,q,s,targets,rotation,SCALE);new=teacher_chunk(task,q,s,targets,rotation,SCALE)
            assert np.array_equal(new[:,2:],old[:,2:])
            if task in [0,1,3]:assert np.array_equal(new,old)
            else:
                expected=np.zeros(2) if armed<.5 or (task==2 and altitude<.25) else -.6*s[:2]
                assert np.allclose(new[:,:2]*SCALE[:2],expected,atol=1e-7)
            checks+=1
with np.load(W/'data/dataset15_en/audited_samples.npz') as d:tasks=d['task'];actions=d['action'];states=d['state']
with np.load(W/'data/dataset14_en/audited_samples.npz') as d:old=d['action']
assert np.array_equal(actions[np.isin(tasks,[0,1,3])],old[np.isin(tasks,[0,1,3])])
assert np.array_equal(actions[:,:,2:],old[:,:,2:])
hold=np.isin(tasks,[2,4,5,6]);s=states[hold];t=tasks[hold]
b=-.6*s[:,:2].astype(float);b[(s[:,8]<.5)|((t==2)&(s[:,3]<.25))]=0
b*=np.minimum(1.,.2/np.maximum(np.linalg.norm(b,axis=1,keepdims=True),1e-12))
assert np.allclose(actions[hold,:,:2]*SCALE[:2],b[:,None,:],rtol=0,atol=1e-6)
r=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,
    plan_sha256=sha(plan),teacher_sha256=sha(W/'scripts/teacher_flight15.py'),dataset_audit_sha256=sha(W/'data/dataset15_en/audit.json'),
    braking_coefficient=BRAKING_COEFFICIENT,synthetic_examples_checked=checks,
    navigation_and_landing_identical=True,nonhorizontal_labels_identical=True,materialized_stationary_targets_checked=True,
    optimization_steps=0,policy_inferences=0,flight_trials=0,
    scope='Teacher synthetic state and materialized target checks, not evidence of learned flight success.')
out.write_text(json.dumps(r,indent=2),encoding='utf8');print(json.dumps(r))
