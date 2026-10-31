"""Check materialized changed labels against the registered scalar teacher."""
import datetime,hashlib,json,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W.parent))
from make_revision_data import rotation,SCALE
from teacher_flight12 import teacher_chunk
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with np.load(W/'data/dataset12_en/audited_samples.npz') as archive:
    a={k:archive[k] for k in archive.files}
    indices=np.flatnonzero(np.isin(a['task'],[2,4,5,6]))
    rng=np.random.default_rng(2026103012);selected=np.sort(rng.choice(indices,2048,replace=False))
    maxima=[]
    for i in selected:
        # Geometry does not affect the changed stationary xy / rotation yaw channels.
        q=np.array([0.,0.,a['state'][i,3],1.,0.,0.,0.]);state=a['state'][i]
        target=teacher_chunk(int(a['task'][i]),q,state,{},rotation,SCALE)
        channels=[0,1]
        if a['task'][i] in [4,5] and state[8]>.5 and state[3]>.8:channels.append(3)
        diff=np.max(np.abs(a['action'][i][:,channels]-target[:,channels]));maxima.append(float(diff))
    assert max(maxima)<1e-6,max(maxima)
out=W/'reports/train12_labels_preflight_audit.json';assert not out.exists()
obj=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,training_examples_checked=2048,seed=2026103012,maximum_absolute_normalized_difference=max(maxima),dataset_audit_sha256=sha(W/'data/dataset12_en/audit.json'),teacher_sha256=sha(W/'scripts/teacher_flight12.py'),scope='Training labels only; no policy inference, optimizer update, flight or evaluation inputs.')
out.write_text(json.dumps(obj,indent=2),encoding='utf8');print(json.dumps(obj))
