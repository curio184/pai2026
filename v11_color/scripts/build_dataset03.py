"""Change only navigation teacher stand-off. Preserve all scorer definitions."""
import hashlib,json,math,shutil,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent;sys.path.insert(0,str(P))
from make_revision_data import rotation,SCALE,scene_targets
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
plan=read(W/'protocol/train03.json');original=read(W/'protocol/plan.json');source=W/'data/dataset02';out=W/'data/dataset03'
assert plan['original_protocol_sha256']==sha(W/'protocol/plan.json')
assert plan['previous_training_plan_sha256']==sha(W/'protocol/train02.json')
for f,h in read(source/'audit.json')['files'].items():assert sha(source/f)==h
out.mkdir(exist_ok=False)
oldcode=(W/'data/dataset/teacher_source.py').read_text(encoding='utf-8');assert oldcode.count('[-.9,0]')==1
newcode=oldcode.replace('[-.9,0]','[-1.0,0]')
namespace=dict(np=np,math=math,rotation=rotation,SCALE=SCALE);exec(oldcode,namespace);oldteacher=namespace['teacher_chunk']
namespace=dict(np=np,math=math,rotation=rotation,SCALE=SCALE);exec(newcode,namespace);newteacher=namespace['teacher_chunk']
(out/'teacher_source.py').write_text(newcode,encoding='utf-8')
frames=read(W/'protocol/training_frames.json');poses=frames+read(P/'outputs/vla_data_realism_precision_02/poses.json')['frames']
targets=[]
for f in frames:
    pos=np.asarray(original['train_layouts'][f['layout']]['positions']);targets.append(dict(blue=pos[f['blue_actor']],red=pos[1-f['blue_actor']]))
targets.extend([scene_targets(W/'scenes/primitive_regression/physics/rescue_scene.xml')]*(len(poses)-len(frames)))
with np.load(source/'audited_samples.npz') as a:arrays={k:a[k].copy() for k in a.files}
oldlabels=arrays['action'].copy();maximum_reconstruction_difference=0.0
for k,(i,t,s) in enumerate(zip(arrays['image'],arrays['task'],arrays['state'])):
    if t>=2:continue
    q=np.asarray(poses[i]['qpos'])
    recovered=oldteacher(t,q,s,targets[i]);delta=float(np.abs(recovered-oldlabels[k]).max());maximum_reconstruction_difference=max(maximum_reconstruction_difference,delta)
    assert delta<1e-5,('Source geometry or teacher mismatch',k,i,delta)
    arrays['action'][k]=newteacher(t,q,s,targets[i])
    if k%10000==0:print('relabel',k,flush=True)
assert np.array_equal(arrays['action'][arrays['task']>=2],oldlabels[arrays['task']>=2])
assert np.array_equal(arrays['action'][:,:,2:],oldlabels[:,:,2:])
assert np.isfinite(arrays['action']).all() and abs(arrays['action']).max()<=1.0001
quartets=np.load(source/'quartets.npy')
for a,b,c,d in quartets:
    assert np.array_equal(arrays['action'][a],arrays['action'][d]) and np.array_equal(arrays['action'][b],arrays['action'][c])
np.savez_compressed(out/'audited_samples.npz',**arrays)
for name in ['quartets.npy','sampling_metadata.npz']:shutil.copy2(source/name,out/name)
manifest=read(source/'manifest.json');manifest.update(teacher_source_sha256=sha(out/'teacher_source.py'),training_plan_sha256=sha(W/'protocol/train03.json'),
    teacher_standoff_m=1.0,scoring_standoff_m=.9,source_dataset_audit_sha256=sha(source/'audit.json'),sampling_pools='Unchanged from train02, indexed by distance to the original 0.9m scoring goal')
write(out/'manifest.json',manifest)
write(out/'audit.json',dict(files={p.name:sha(p) for p in out.iterdir() if p.is_file()},image_checksums_source='../dataset/image_checksums.json',
    pixels_changed=False,plan_sha256=sha(W/'protocol/train03.json'),inputs=['image','task','state'],target='action',
    development_or_heldout_images_used=0,source_teacher_max_reconstruction_error=maximum_reconstruction_difference,
    non_navigation_labels_unchanged=True,non_horizontal_labels_unchanged=True,all_counterfactual_labels_swapped_exactly=True))
print(json.dumps(dict(samples=len(arrays['task']),relabelled_navigation=int((arrays['task']<2).sum()),max_source_reconstruction_error=maximum_reconstruction_difference,scoring_unchanged=True)))
