"""Frozen training plan: paired shirt interventions, never evaluation imagery."""
import hashlib, json, math, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parents[1]; P=W.parent
sys.path.insert(0,str(P))
from make_revision_data import rotation, visible, SCALE
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
plan=json.loads((W/'protocol/plan.json').read_text(encoding='utf-8'))
assert sha(W/'protocol/plan.json')=='ed157f5a14536772d05a00cfe31c315f6b747d624da4b527e8ce5e64de5cd111'
assert sha(W/'protocol/training_frames.json')=='5feb124fd61ea9ae8368703ee8100395b79c7275e54611091dbc901ac18d12a1'
frames=json.loads((W/'protocol/training_frames.json').read_text(encoding='utf-8'))
old=P/'outputs/vla_data_realism_precision_02'; out=W/'data/dataset'
assert all((W/'data/rendered_png'/f'{i:05d}.png').is_file() for i in range(len(frames)))
out.mkdir(exist_ok=False);(out/'images').mkdir()
source=(old/'teacher_source.py').read_text(encoding='utf-8')
assert sha(old/'teacher_source.py')=='ec117743d58e9c200661b170acca57060fdb00424e36e464408a49a7da2e7687'
assert '>.04' in source or '>0.04' in source
exec(compile(source,str(old/'teacher_source.py'),'exec'),globals())
(out/'teacher_source.py').write_text(source,encoding='utf-8')
rng=np.random.default_rng(plan['training']['seed']); ids=[]; tasks=[]; states=[]; labels=[]; nav={}; hashes={}
def add(i,t,q,s,targets):
    j=len(tasks);ids.append(i);tasks.append(t);states.append(s.copy());labels.append(teacher_chunk(t,q,s,targets));return j
for f in frames:
    i=f['id']; dest=out/'images'/f'{i:05d}.jpg'
    Image.open(W/'data/rendered_png'/f'{i:05d}.png').convert('RGB').save(dest,quality=70)
    hashes[dest.name]=sha(dest)
    q=np.asarray(f['qpos']);s=np.asarray(f['state'],dtype=np.float32)
    positions=np.asarray(plan['train_layouts'][f['layout']]['positions'])
    targets={'blue':positions[f['blue_actor']],'red':positions[1-f['blue_actor']]}
    nav[i]=[]
    for t,c in enumerate(['blue','red']):
        allowed=s[3]<=.8 or visible(q,targets[c])
        nav[i].append(add(i,t,q,s,targets) if allowed else -1)
    for t in range(2,7):
        own=s.copy()
        if t in [4,5] and s[3]>.8:
            own[6]=(1 if t==4 else -1)*rng.uniform(-.2,math.pi/2+.25);own[7]=rng.uniform(-.35,.35)
        add(i,t,q,own,targets)
        if t in [4,5] and s[3]>.8:
            own=s.copy();own[6]=(math.pi/2 if t==4 else -math.pi/2)+rng.uniform(-.12,.12);own[7]=rng.uniform(-.08,.08)
            add(i,t,q,own,targets)
    if i%500==0:print('labels',i,len(tasks),flush=True)
new_count=len(tasks)
quartets=[]; pairs=[]
for i in range(0,len(frames),2):
    assert frames[i]['qpos']==frames[i+1]['qpos'] and frames[i]['state']==frames[i+1]['state']
    if min(nav[i]+nav[i+1])>=0 and frames[i]['state'][3]>.8:
        quartets.append(nav[i]+nav[i+1])
for i in range(len(frames)):
    if min(nav[i])>=0 and frames[i]['state'][3]>.8:pairs.append(nav[i])
assert len(quartets)>100
old_audit=json.loads((old/'audit.json').read_text(encoding='utf-8'))
assert sha(old/'audited_samples.npz')==old_audit['sha256']
old_hash=json.loads((old/'image_checksums.json').read_text(encoding='utf-8'))
for name,h in old_hash.items():
    assert sha(old/'images'/name)==h
    dest=out/'images'/f'{int(Path(name).stem)+len(frames):05d}.jpg'
    shutil.copy2(old/'images'/name,dest);hashes[dest.name]=h
with np.load(old/'audited_samples.npz') as a:
    arrays=dict(image=np.r_[np.asarray(ids,dtype=np.int32),a['image']+len(frames)],task=np.r_[np.asarray(tasks,dtype=np.int16),a['task']],
                state=np.concatenate([np.asarray(states,dtype=np.float32),a['state']]),action=np.concatenate([np.asarray(labels,dtype=np.float32),a['action']]))
for a,b,c,d in quartets:
    assert np.array_equal(arrays['state'][a],arrays['state'][d])
    assert np.array_equal(arrays['action'][a],arrays['action'][d]) and np.array_equal(arrays['action'][b],arrays['action'][c])
assert np.isfinite(arrays['action']).all() and abs(arrays['action']).max()<=1.0001
np.savez_compressed(out/'audited_samples.npz',**arrays)
np.save(out/'quartets.npy',np.asarray(quartets,dtype=np.int32));np.save(out/'new_nav_pairs.npy',np.asarray(pairs,dtype=np.int32))
np.save(out/'old_nav_pairs.npy',np.load(old/'nav_pairs.npy')+new_count)
write(out/'image_checksums.json',hashes)
prompts=json.loads((old/'manifest.json').read_text(encoding='utf-8'))['prompts']
variants=[[s,s.split('. ',1)[1],s.split('. ',1)[0]+'.'] for s in prompts]
write(out/'manifest.json',dict(prompts=prompts,prompt_variants=variants,new_sample_count=new_count,new_images=len(frames),retention_images=len(old_hash),
    samples=len(arrays['task']),quartets=len(quartets),new_nav_pairs=len(pairs),
    teacher_only='Positions and layout IDs used for synthetic labels only; absent from audited model input archive.',
    source_retention_sha256=old_audit['sha256'],plan_sha256=sha(W/'protocol/plan.json'),teacher_source_sha256=sha(out/'teacher_source.py')))
audit={p.name:sha(p) for p in out.iterdir() if p.is_file()}
write(out/'audit.json',dict(files=audit,task_counts=np.bincount(arrays['task'],minlength=7).tolist(),all_counterfactual_labels_swapped_exactly=True,
    no_teacher_geometry_in_npz=True,inputs=['image','task','state'],target='action',images_hashed=len(hashes)))
print(json.dumps(dict(samples=len(arrays['task']),quartets=len(quartets),images=len(hashes))),flush=True)
