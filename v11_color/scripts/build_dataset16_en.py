"""Relabel stationary horizontal outputs after preregistration, preserving inputs."""
import hashlib
import json
import shutil
import sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(W.parent))
from make_revision_data import SCALE
from teacher_flight16 import VELOCITY_RETENTION,ATTITUDE_RETENTION,GRAVITY
def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,indent=2),encoding='utf8')

planfile=W/'protocol/train16_english.json'
plan=read(planfile)
source=W/'data/dataset15_en'
out=W/'data/dataset16_en'
assert not out.exists()
assert sha(source/'audit.json')==plan['data']['source_audit_sha256']
assert sha(W/'scripts/teacher_flight16.py')==plan['teacher_source_sha256']
for f,h in read(source/'audit.json')['files'].items(): assert sha(source/f)==h,f
sources=read(source/'image_sources.json')
assert len(sources)==8408
for row in sources: assert sha(W/row['path'])==row['sha256']
with np.load(source/'audited_samples.npz') as d: base={k:d[k].copy() for k in d.files}
inputs={k:hashlib.sha256(base[k].tobytes()).hexdigest() for k in ['image','task','state']}
old=base['action'].copy()
hold=np.flatnonzero(np.isin(base['task'],[2,4,5,6]))
s=base['state'][hold].astype(float)
t=base['task'][hold]
valid=(s[:,8]>.5)&~((t==2)&(s[:,3]<.25))
prior=-.6*s[:,:2]
prior[~valid]=0
prior*=np.minimum(1.,.2/np.maximum(np.linalg.norm(prior,axis=1,keepdims=True),1e-12))
assert np.allclose(old[hold,:,:2]*SCALE[:2],prior[:,None,:],rtol=0,atol=1e-6)
request=VELOCITY_RETENTION*s[:,:2]-ATTITUDE_RETENTION*GRAVITY*np.tan(s[:,[5,4]])
request[~valid]=0
request*=np.minimum(1.,.2/np.maximum(np.linalg.norm(request,axis=1,keepdims=True),1e-12))
base['action'][hold,:,:2]=(request/np.asarray(SCALE[:2])).astype(np.float32)[:,None,:]
assert np.array_equal(base['action'][base['task']<2],old[base['task']<2])
assert np.array_equal(base['action'][base['task']==3],old[base['task']==3])
assert np.array_equal(base['action'][:,:,2:],old[:,:,2:])
assert all(hashlib.sha256(base[k].tobytes()).hexdigest()==h for k,h in inputs.items())
for a,b,c,d in np.load(source/'quartets.npy'):
    assert np.array_equal(base['action'][a],base['action'][d])
    assert np.array_equal(base['action'][b],base['action'][c])
assert np.isfinite(base['action']).all()
assert np.max(np.linalg.norm(base['action'][:,:,:2]*SCALE[:2],axis=-1))<=.200001
out.mkdir()
np.savez_compressed(out/'audited_samples.npz',**base)
for name in ['quartets.npy','state_pairs.npy','state_quartets.npy','image_sources.json','sampling_metadata.npz']:
    shutil.copy2(source/name,out/name)
shutil.copy2(W/'scripts/teacher_flight16.py',out/'teacher_source.py')
m=read(source/'manifest.json')
m.pop('braking_coefficient',None)
m.update(stationary_teacher='leaky attitude-assisted request',velocity_retention=VELOCITY_RETENTION,
    attitude_retention=ATTITUDE_RETENTION,gravity_m_s2=GRAVITY,
    training_plan_sha256=sha(planfile),source_dataset_audit_sha256=sha(source/'audit.json'),
    teacher_source_sha256=sha(out/'teacher_source.py'),added_images=0,added_state_examples=0)
write(out/'manifest.json',m)
write(out/'audit.json',dict(files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
    plan_sha256=sha(planfile),inputs=['image','task','state'],target='action',input_arrays_sha256=inputs,
    images_unchanged=True,states_unchanged=True,prompts_unchanged=True,
    navigation_labels_byte_identical=True,landing_labels_byte_identical=True,nonhorizontal_labels_byte_identical=True,
    relabeled_stationary_examples=len(hold),all_counterfactual_labels_swapped_exactly=True,
    evaluation_images_or_states_used_for_training=0,teacher_geometry_in_model_npz=False))
print(json.dumps(dict(samples=len(base['task']),stationary=len(hold),images=len(sources),audit_sha256=sha(out/'audit.json'))))
