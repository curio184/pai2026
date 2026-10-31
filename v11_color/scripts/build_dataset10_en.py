"""Relabel airborne rotation yaw only under the train10 preregistration."""
import hashlib,json,math,shutil,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W.parent))
from make_revision_data import SCALE
from teacher_flight10 import YAW_DEADBAND_RAD,YAW_GAIN
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf8')
planfile=W/'protocol/train10_english.json';plan=read(planfile)
source=W/'data/dataset09_en';out=W/'data/dataset10_en';assert not out.exists()
assert sha(source/'audit.json')==plan['data']['source_audit_sha256']
assert sha(W/'scripts/teacher_flight10.py')==plan['teacher_source_sha256']
assert YAW_DEADBAND_RAD==plan['teacher']['yaw_deadband_rad']==.03
assert YAW_GAIN==plan['teacher']['yaw_gain']==.8
for f,h in read(source/'audit.json')['files'].items():assert sha(source/f)==h,f
sources=read(source/'image_sources.json')
for row in sources:assert sha(W/row['path'])==row['sha256']
with np.load(source/'audited_samples.npz') as d:base={k:d[k].copy() for k in d.files}
inputs={k:hashlib.sha256(base[k].tobytes()).hexdigest() for k in ['image','task','state']}
old=base['action'].copy()
eligible=np.isin(base['task'],[4,5])&(base['state'][:,8]>.5)&(base['state'][:,3]>.8)
yaw=base['state'][eligible,6].astype(np.float64)
target=np.where(base['task'][eligible]==4,math.pi/2,-math.pi/2)
for k in range(base['action'].shape[1]):
    error=target-yaw
    rate=np.where(np.abs(error)<YAW_DEADBAND_RAD,0.,np.clip(YAW_GAIN*error,-.35,.35))
    base['action'][eligible,k,3]=rate/SCALE[3]
    yaw+=.1*rate
assert np.array_equal(base['action'][:,:,[0,1,2,4,5]],old[:,:,[0,1,2,4,5]])
assert np.array_equal(base['action'][~eligible],old[~eligible])
assert all(hashlib.sha256(base[k].tobytes()).hexdigest()==h for k,h in inputs.items())
for a,b,c,d in np.load(source/'quartets.npy'):
    assert np.array_equal(base['action'][a],base['action'][d]) and np.array_equal(base['action'][b],base['action'][c])
assert np.isfinite(base['action']).all()
assert np.max(np.abs(base['action'][eligible,:,3]*SCALE[3]))<=.350001
out.mkdir();np.savez_compressed(out/'audited_samples.npz',**base)
for name in ['quartets.npy','state_pairs.npy','state_quartets.npy','image_sources.json','sampling_metadata.npz']:shutil.copy2(source/name,out/name)
shutil.copy2(W/'scripts/teacher_flight10.py',out/'teacher_source.py')
m=read(source/'manifest.json');m.update(yaw_deadband_rad=.03,yaw_gain=.8,
    training_plan_sha256=sha(planfile),source_dataset_audit_sha256=sha(source/'audit.json'),
    teacher_source_sha256=sha(out/'teacher_source.py'),added_images=0,added_state_examples=0)
write(out/'manifest.json',m)
write(out/'audit.json',dict(files={p.name:sha(p) for p in out.iterdir() if p.is_file()},plan_sha256=sha(planfile),
    inputs=['image','task','state'],target='action',input_arrays_sha256=inputs,
    images_unchanged=True,states_unchanged=True,prompts_unchanged=True,
    non_yaw_labels_byte_identical=True,noneligible_labels_byte_identical=True,
    navigation_and_landing_labels_byte_identical=True,
    yaw_deadband_rad=.03,relabeled_examples=int(eligible.sum()),
    all_counterfactual_labels_swapped_exactly=True,evaluation_images_or_states_used_for_training=0,
    teacher_geometry_in_model_npz=False))
print(json.dumps(dict(samples=len(base['task']),relabeled_rotation_examples=int(eligible.sum()),images=len(sources),audit_sha256=sha(out/'audit.json'))))
