"""Relabel only stationary xy and rotation yaw under the train12 plan."""
import hashlib,json,math,shutil,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W.parent))
from make_revision_data import SCALE
from teacher_flight12 import BRAKING_COEFFICIENT,YAW_CAP_RAD_S,YAW_CAPTURE_LOOKAHEAD_S,YAW_DEADBAND_RAD,YAW_GAIN
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf8')
planfile=W/'protocol/train12_english.json';plan=read(planfile)
source=W/'data/dataset10_en';out=W/'data/dataset12_en';assert not out.exists()
assert sha(source/'audit.json')==plan['data']['source_audit_sha256']
assert sha(W/'scripts/teacher_flight12.py')==plan['teacher_source_sha256']
assert BRAKING_COEFFICIENT==plan['teacher']['braking_coefficient']==1.2
assert YAW_CAPTURE_LOOKAHEAD_S==plan['teacher']['yaw_capture_lookahead_s']==1.0
assert YAW_CAP_RAD_S==plan['teacher']['yaw_cap_rad_s']==.25
for f,h in read(source/'audit.json')['files'].items():assert sha(source/f)==h,f
sources=read(source/'image_sources.json')
for row in sources:assert sha(W/row['path'])==row['sha256']
with np.load(source/'audited_samples.npz') as d:base={k:d[k].copy() for k in d.files}
inputs={k:hashlib.sha256(base[k].tobytes()).hexdigest() for k in ['image','task','state']}
old=base['action'].copy();states=base['state'];tasks=base['task']
stationary=np.isin(tasks,[2,4,5,6]);active=stationary&(states[:,8]>.5)&~((tasks==2)&(states[:,3]<.25))
brake=-BRAKING_COEFFICIENT*states[active,:2].astype(np.float64)
brake*=np.minimum(1.,.2/np.maximum(np.linalg.norm(brake,axis=1),1e-12))[:,None]
base['action'][stationary,:,:2]=0
base['action'][active,:,:2]=(brake/np.asarray(SCALE[:2]))[:,None,:]
rotating=np.isin(tasks,[4,5])&(states[:,8]>.5)&(states[:,3]>.8)
yaw=states[rotating,6].astype(np.float64)+YAW_CAPTURE_LOOKAHEAD_S*states[rotating,7]
target=np.where(tasks[rotating]==4,math.pi/2,-math.pi/2)
for k in range(base['action'].shape[1]):
    error=target-yaw;rate=np.where(np.abs(error)<YAW_DEADBAND_RAD,0.,np.clip(YAW_GAIN*error,-YAW_CAP_RAD_S,YAW_CAP_RAD_S))
    base['action'][rotating,k,3]=rate/SCALE[3];yaw+=.1*rate
assert np.array_equal(base['action'][:,:,[2,4,5]],old[:,:,[2,4,5]])
assert np.array_equal(base['action'][~stationary,:,:2],old[~stationary,:,:2])
assert np.array_equal(base['action'][~rotating,:,3],old[~rotating,:,3])
assert np.array_equal(base['action'][np.isin(tasks,[0,1,3])],old[np.isin(tasks,[0,1,3])])
assert all(hashlib.sha256(base[k].tobytes()).hexdigest()==h for k,h in inputs.items())
for a,b,c,d in np.load(source/'quartets.npy'):
    assert np.array_equal(base['action'][a],base['action'][d]) and np.array_equal(base['action'][b],base['action'][c])
assert np.isfinite(base['action']).all()
assert np.max(np.linalg.norm(base['action'][stationary,:,:2]*np.asarray(SCALE[:2]),axis=-1))<=.200001
assert np.max(np.abs(base['action'][rotating,:,3]*SCALE[3]))<=.250001
out.mkdir();np.savez_compressed(out/'audited_samples.npz',**base)
for name in ['quartets.npy','state_pairs.npy','state_quartets.npy','image_sources.json','sampling_metadata.npz']:shutil.copy2(source/name,out/name)
shutil.copy2(W/'scripts/teacher_flight12.py',out/'teacher_source.py')
m=read(source/'manifest.json');m.update(braking_coefficient=1.2,yaw_deadband_rad=.03,yaw_gain=.8,yaw_cap_rad_s=.25,yaw_capture_lookahead_s=1.0,training_plan_sha256=sha(planfile),source_dataset_audit_sha256=sha(source/'audit.json'),teacher_source_sha256=sha(out/'teacher_source.py'),added_images=0,added_state_examples=0)
write(out/'manifest.json',m)
write(out/'audit.json',dict(files={p.name:sha(p) for p in out.iterdir() if p.is_file()},plan_sha256=sha(planfile),inputs=['image','task','state'],target='action',input_arrays_sha256=inputs,images_unchanged=True,states_unchanged=True,prompts_unchanged=True,vertical_and_requests_byte_identical=True,navigation_and_landing_labels_byte_identical=True,relabeled_stationary_examples=int(stationary.sum()),relabeled_rotation_examples=int(rotating.sum()),all_counterfactual_labels_swapped_exactly=True,evaluation_images_or_states_used_for_training=0,teacher_geometry_in_model_npz=False))
print(json.dumps(dict(samples=len(tasks),stationary=int(stationary.sum()),rotating=int(rotating.sum()),images=len(sources),audit_sha256=sha(out/'audit.json'))))
