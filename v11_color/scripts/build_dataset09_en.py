"""Apply the preregistered mild braking labels; preserve all inputs and navigation."""
import hashlib,json,shutil,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W.parent))
from make_revision_data import SCALE
from teacher_flight09 import BRAKING_COEFFICIENT
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf8')

planfile=W/'protocol/train09_english.json';plan=read(planfile)
source=W/'data/dataset08_en';out=W/'data/dataset09_en';assert not out.exists()
assert sha(source/'audit.json')==plan['data']['source_audit_sha256']
assert sha(W/'scripts/teacher_flight09.py')==plan['teacher_source_sha256']
assert BRAKING_COEFFICIENT==plan['training']['braking_coefficient']==.6
for f,h in read(source/'audit.json')['files'].items():assert sha(source/f)==h,f
sources=read(source/'image_sources.json')
for row in sources:assert sha(W/row['path'])==row['sha256']
with np.load(source/'audited_samples.npz') as d:base={k:d[k].copy() for k in d.files}
inputs={k:hashlib.sha256(base[k].tobytes()).hexdigest() for k in ['image','task','state']}
old=base['action'].copy();eligible=np.isin(base['task'],[2,4,5,6])
brake=-BRAKING_COEFFICIENT*base['state'][eligible,:2].astype(np.float64)
unarmed=base['state'][eligible,8]<=.5
grounded_takeoff=(base['task'][eligible]==2)&(base['state'][eligible,3]<.25)
brake[unarmed|grounded_takeoff]=0
brake*=np.minimum(1.,.2/np.maximum(np.linalg.norm(brake,axis=1,keepdims=True),1e-12))
base['action'][eligible,:,:2]=brake[:,None,:]/SCALE[:2]
assert np.array_equal(base['action'][:,:,2:],old[:,:,2:])
assert np.array_equal(base['action'][~eligible],old[~eligible])
assert all(hashlib.sha256(base[k].tobytes()).hexdigest()==h for k,h in inputs.items())
for a,b,c,d in np.load(source/'state_quartets.npy'):
    assert np.array_equal(base['action'][a,:,:2],-base['action'][b,:,:2])
    assert np.count_nonzero(base['action'][c,:,:2])==0
for a,b,c,d in np.load(source/'quartets.npy'):
    assert np.array_equal(base['action'][a],base['action'][d]) and np.array_equal(base['action'][b],base['action'][c])
assert np.isfinite(base['action']).all() and np.linalg.norm(base['action'][:,:,:2]*SCALE[:2],axis=2).max()<=.200001
out.mkdir();np.savez_compressed(out/'audited_samples.npz',**base)
for name in ['quartets.npy','state_pairs.npy','state_quartets.npy','image_sources.json','sampling_metadata.npz']:shutil.copy2(source/name,out/name)
shutil.copy2(W/'scripts/teacher_flight09.py',out/'teacher_source.py')
m=read(source/'manifest.json');m.update(braking_coefficient=.6,grounded_takeoff_horizontal_zero_below_m=.25,
    training_plan_sha256=sha(planfile),source_dataset_audit_sha256=sha(source/'audit.json'),
    teacher_source_sha256=sha(out/'teacher_source.py'),added_images=0,added_state_examples=0)
write(out/'manifest.json',m)
write(out/'audit.json',dict(files={p.name:sha(p) for p in out.iterdir() if p.is_file()},plan_sha256=sha(planfile),
    inputs=['image','task','state'],target='action',input_arrays_sha256=inputs,
    images_unchanged=True,states_unchanged=True,prompts_unchanged=True,
    navigation_and_landing_labels_byte_identical=True,nonhorizontal_existing_labels_byte_identical=True,
    hold_teacher_coefficient=.6,grounded_takeoff_zero=True,state_pairs_opposite=True,
    all_counterfactual_labels_swapped_exactly=True,evaluation_images_or_states_used_for_training=0,
    teacher_geometry_in_model_npz=False))
print(json.dumps(dict(samples=len(base['task']),relabeled_stationary_examples=int(eligible.sum()),images=len(sources),audit_sha256=sha(out/'audit.json'))))
