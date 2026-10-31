"""Add own-state coverage and explicit near-goal pools; pixels and teacher unchanged."""
import hashlib,json,math,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent;sys.path.insert(0,str(P))
from make_revision_data import rotation,visible,SCALE,scene_targets
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
plan=read(W/'protocol/train02.json');original=read(W/'protocol/plan.json')
assert plan['original_protocol_sha256']==sha(W/'protocol/plan.json')
source=W/'data/dataset';out=W/'data/dataset02';out.mkdir(exist_ok=False)
for f,h in read(source/'audit.json')['files'].items():assert sha(source/f)==h
teacher=source/'teacher_source.py';exec(compile(teacher.read_text(encoding='utf-8'),str(teacher),'exec'),globals())
frames=read(W/'protocol/training_frames.json');oldposes=read(P/'outputs/vla_data_realism_precision_02/poses.json')['frames']
assert len(frames)==4000 and len(oldposes)==2408
oldtargets=scene_targets(W/'scenes/primitive_regression/physics/rescue_scene.xml')
allposes=frames+oldposes;targets=[]
for f in frames:
    pos=np.asarray(original['train_layouts'][f['layout']]['positions'])
    targets.append(dict(blue=pos[f['blue_actor']],red=pos[1-f['blue_actor']]))
targets.extend([oldtargets]*len(oldposes))
with np.load(source/'audited_samples.npz') as a:base={k:a[k].copy() for k in a.files}
ids=[];tasks=[];states=[];labels=[];mapping={};rng=np.random.default_rng(plan['training']['seed'])
variants={}
for i,f in enumerate(allposes):
    if f['state'][3]<=.8:continue
    key=i//2 if i<4000 else i
    domain=0 if i<4000 else 1
    if (domain,key) not in variants:
        vv=[]
        for j in range(3):
            angle=rng.uniform(-math.pi,math.pi);radius=0 if j==0 else .26*math.sqrt(rng.uniform())
            vv.append([radius*math.cos(angle),radius*math.sin(angle),rng.uniform(-.06,.06)])
        variants[domain,key]=vv
    q=np.asarray(f['qpos']);own=np.asarray(f['state'],dtype=np.float32)
    for j,v in enumerate(variants[domain,key]):
        state=own.copy();state[:2]=v[:2];state[6]=v[2]
        for t,c in enumerate(['blue','red']):
            if not visible(q,targets[i][c]):continue
            index=len(base['task'])+len(tasks);mapping[i,j,t]=index
            ids.append(i);tasks.append(t);states.append(state.copy());labels.append(teacher_chunk(t,q,state,targets[i]))
arrays=dict(image=np.r_[base['image'],np.asarray(ids,dtype=np.int32)],task=np.r_[base['task'],np.asarray(tasks,dtype=np.int16)],
            state=np.concatenate([base['state'],np.asarray(states,dtype=np.float32)]),action=np.concatenate([base['action'],np.asarray(labels,dtype=np.float32)]))
quartets=np.load(source/'quartets.npy').tolist()
for i in range(0,4000,2):
    for j in range(3):
        keys=[(i,j,0),(i,j,1),(i+1,j,0),(i+1,j,1)]
        if all(k in mapping for k in keys):quartets.append([mapping[k] for k in keys])
distance=np.full(len(arrays['task']),np.nan,dtype=np.float32)
for k,(i,t) in enumerate(zip(arrays['image'],arrays['task'])):
    if t<2:distance[k]=np.linalg.norm(targets[i][['blue','red'][t]][:2]+[-.9,0]-np.asarray(allposes[i]['qpos'])[:2])
domain=(arrays['image']>=4000).astype(np.int8)
for a,b,c,d in quartets:
    assert np.array_equal(arrays['state'][a],arrays['state'][d])
    assert np.array_equal(arrays['action'][a],arrays['action'][d]) and np.array_equal(arrays['action'][b],arrays['action'][c])
assert np.isfinite(arrays['state']).all() and np.isfinite(arrays['action']).all() and abs(arrays['action']).max()<=1.0001
np.savez_compressed(out/'audited_samples.npz',**arrays)
np.save(out/'quartets.npy',np.asarray(quartets,dtype=np.int32))
np.savez_compressed(out/'sampling_metadata.npz',domain=domain,goal_distance=distance)
counts={}
for dom in [0,1]:
    for t in [0,1]:
        eligible=(domain==dom)&(arrays['task']==t)&(arrays['state'][:,3]>.8)
        counts[f'{dom}_{t}']=dict(all=int(eligible.sum()),near=int((eligible&(distance<=.65)).sum()))
        assert counts[f'{dom}_{t}']['near']>100
manifest=read(source/'manifest.json');manifest.update(samples=len(arrays['task']),quartets=len(quartets),
    image_directory='../dataset/images',source_dataset_audit_sha256=sha(source/'audit.json'),augmentation_plan_sha256=sha(W/'protocol/train02.json'),
    additional_examples=len(tasks),navigation_pool_counts=counts,geometry_not_model_input=True)
write(out/'manifest.json',manifest)
write(out/'audit.json',dict(files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
    image_checksums_source='../dataset/image_checksums.json',pixels_changed=False,teacher_sha256=sha(teacher),
    plan_sha256=sha(W/'protocol/train02.json'),inputs=['image','task','state'],target='action',metadata_not_passed_to_model=True,
    development_or_heldout_images_used=0,source_poses_sha256=sha(P/'outputs/vla_data_realism_precision_02/poses.json')))
print(json.dumps(dict(samples=manifest['samples'],added=len(tasks),quartets=len(quartets),pools=counts)))
