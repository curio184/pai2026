"""Relabel existing training data only under the preregistered train07 recipe."""
import hashlib,json,shutil,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent;sys.path.insert(0,str(P))
from make_revision_data import rotation,SCALE,scene_targets
from teacher_flight06 import teacher_chunk as oldteacher
from teacher_flight07 import teacher_chunk as teacher
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf8')
planfile=W/'protocol/train07_english.json';plan=read(planfile)
source=W/'data/dataset06_en';out=W/'data/dataset07_en';assert not out.exists()
assert sha(source/'audit.json')==plan['data']['source_audit_sha256']
assert sha(W/'scripts/teacher_flight07.py')==plan['teacher_source_sha256']
for f,h in read(source/'audit.json')['files'].items():assert sha(source/f)==h,f
original=read(W/'protocol/plan.json')
frames=read(W/'protocol/training_frames.json');retained=read(P/'outputs/vla_data_realism_precision_02/poses.json')['frames']
extra=read(W/'protocol/train05_training_frames.json');poses=frames+retained+extra
targets=[]
for f in frames:
    pos=np.asarray(original['train_layouts'][f['layout']]['positions']);targets.append(dict(blue=pos[f['blue_actor']],red=pos[1-f['blue_actor']]))
targets.extend([scene_targets(W/'scenes/primitive_regression/physics/rescue_scene.xml')]*len(retained))
for f in extra:
    pos=np.asarray(original['train_layouts'][f['layout']]['positions']);targets.append(dict(blue=pos[f['blue_actor']],red=pos[1-f['blue_actor']]))
sources=read(source/'image_sources.json');assert len(sources)==len(poses)==8408
for row in sources:assert sha(W/row['path'])==row['sha256']
with np.load(source/'audited_samples.npz') as d:base={k:d[k].copy() for k in d.files}
nonhorizontal=hashlib.sha256(base['action'][:,:,2:].tobytes()).hexdigest()
nav=np.flatnonzero(base['task']<2);maximum=0.
for count,k in enumerate(nav):
    i=int(base['image'][k]);t=int(base['task'][k]);s=base['state'][k];q=np.asarray(poses[i]['qpos'])
    old=oldteacher(t,q,s,targets[i],rotation,SCALE)
    diff=float(np.abs(old-base['action'][k]).max());maximum=max(maximum,diff);assert diff<1e-5
    new=teacher(t,q,s,targets[i],rotation,SCALE)
    assert np.array_equal(new[:,2:],base['action'][k,:,2:])
    base['action'][k,:,:2]=new[:,:2]
    if count%5000==0:print(json.dumps(dict(navigation=count,total=len(nav))),flush=True)
base['action'][np.isin(base['task'],[2,4,5,6]),:,:2]=0.
assert hashlib.sha256(base['action'][:,:,2:].tobytes()).hexdigest()==nonhorizontal
for a,b,c,d in np.load(source/'quartets.npy'):
    assert np.array_equal(base['action'][a],base['action'][d]) and np.array_equal(base['action'][b],base['action'][c])
assert np.isfinite(base['action']).all()
assert np.linalg.norm(base['action'][:,:,:2]*SCALE[:2],axis=2).max()<=.200001
out.mkdir();np.savez_compressed(out/'audited_samples.npz',**base)
for name in ['quartets.npy','state_pairs.npy','state_quartets.npy','image_sources.json','sampling_metadata.npz']:shutil.copy2(source/name,out/name)
shutil.copy2(W/'scripts/teacher_flight07.py',out/'teacher_source.py')
m=read(source/'manifest.json');m.update(braking_coefficient=0.,teacher_standoff_m=.9,
    navigation_position_coefficient=1.4,additional_state_examples=0,additional_images=0,
    training_plan_sha256=sha(planfile),source_dataset_audit_sha256=sha(source/'audit.json'),teacher_source_sha256=sha(out/'teacher_source.py'))
m.pop('grounded_takeoff_horizontal_zero_below_m',None)
write(out/'manifest.json',m)
write(out/'audit.json',dict(files={p.name:sha(p) for p in out.iterdir() if p.is_file()},plan_sha256=sha(planfile),
    source_teacher_max_reconstruction_error=maximum,inputs=['image','task','state'],target='action',
    evaluation_images_or_states_used_for_training=0,images_unchanged=True,states_unchanged=True,
    nonhorizontal_existing_labels_byte_identical=True,all_counterfactual_labels_swapped_exactly=True,
    hold_horizontal_labels_zero=True,teacher_geometry_in_model_npz=False))
print(json.dumps(dict(samples=len(base['task']),images=8408,audit_sha256=sha(out/'audit.json'))))
