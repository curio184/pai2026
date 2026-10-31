"""Preregister training-input fit diagnostics before any policy inference."""
import datetime,hashlib,json
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
data=W/'data/dataset13_en';audit=read(data/'audit.json')
for name,h in audit['files'].items():assert sha(data/name)==h
with np.load(data/'audited_samples.npz') as a:
    task=a['task'];state=a['state'];image=a['image']
with np.load(data/'sampling_metadata.npz') as a:distance=a['goal_distance']
rng=np.random.default_rng(2026103014);selected=[]
for t in range(7):
    for group in range(2):
        base=task==t
        if t in [0,1]:
            base&=(state[:,8]>.5)&(state[:,3]>.8)
            base&=(distance<=.4) if group==0 else (distance>.65)
            label='near_goal' if group==0 else 'far_goal'
        elif t==2:
            base&=(state[:,8]<.5) if group==0 else (state[:,8]>.5)
            label='unarmed' if group==0 else 'armed'
        else:
            speed=np.linalg.norm(state[:,:2],axis=1)
            base&=(speed<=.08) if group==0 else (speed>.08)
            label='low_estimated_speed' if group==0 else 'higher_estimated_speed'
        pool=np.flatnonzero(base);assert len(pool)>=8,(t,group,len(pool))
        for idx in sorted(rng.choice(pool,size=8,replace=False).tolist()):
            selected.append(dict(sample_index=idx,image_index=int(image[idx]),task=t,stratum=label))
assert len(selected)==112 and len(set(x['sample_index'] for x in selected))==112
result=read(W/'models/train13_en/result.json')
plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train13_en',
    checkpoint_sha256=result['checkpoint_sha256'],dataset_audit_sha256=sha(data/'audit.json'),seed=2026103014,
    selected=selected,prompt_variant=2,runtime_noise_seed=20261024,
    inference_steps=[10,1],
    inference_scope='Ten steps reproduces deployed inference. One step is an offline diagnostic only; no inference-step choice will be made for runtime and no flight settings are changed.',
    selection='Eight samples from each of two predefined strata per task, sampled without replacement from audited training data before policy inference. No evaluation image/state is used.',
    metrics='Per-axis absolute error against the stored teacher chunk in physical units, first10 and full32 means; first10 horizontal vector RMSE; all112 outputs retained for both step counts.',
    limitations='Training-set fit diagnostic, not held-out performance, not a flight result, and not a unique causal explanation. Unobserved runtime states can still fail.',
    runner_sha256=sha(W/'scripts/run_train13_fit_diagnostic.py'),registration_script_sha256=sha(Path(__file__)),
    resource_rule='Run after the current flight pipeline is terminal; Windows GPU only. No optimization or model writes.')
dest=W/'protocol/train13_fit_diagnostic.json';assert not dest.exists();dest.write_text(json.dumps(plan,indent=2),encoding='utf8')
print(json.dumps(dict(plan=str(dest),sha256=sha(dest),samples=len(selected),policy_inferences=0)))
