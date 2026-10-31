"""Inspect existing training coverage without inference or new evaluation."""
import json, math, hashlib
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
with np.load(W/'data/dataset09_en/audited_samples.npz') as d:
    task=d['task'];state=d['state'];action=d['action'];images=d['image']
rows=[]
for t,target in [(4,math.pi/2),(5,-math.pi/2)]:
    valid=(task==t)&(state[:,8]>.5)&(state[:,3]>.8)
    errors=target-state[:,6]
    bins=[]
    for lo,hi in [(-.4,-.2),(-.2,-.12),(-.12,-.03),(-.03,.03),(.03,.12),(.12,.2),(.2,.4)]:
        use=valid&(errors>=lo)&(errors<hi)
        bins.append(dict(error_rad=[lo,hi],examples=int(use.sum()),unique_images=len(set(images[use].tolist()))))
    rows.append(dict(task=t,examples=int(valid.sum()),error_bins=bins))
out=W/'reports/train09_rotation_training_coverage.json';assert not out.exists()
obj=dict(scope='Existing training data only; no inference or evaluation.',rows=rows)
out.write_text(json.dumps(obj,indent=2),encoding='utf-8');print(json.dumps(obj))
