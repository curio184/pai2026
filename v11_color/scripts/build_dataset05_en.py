"""Train05: keep all old pixels/labels, add registered views and opposite-own-velocity pairs."""
import hashlib,json,math,shutil,sys
from pathlib import Path
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parents[1];P=W.parent;sys.path.insert(0,str(P))
from make_revision_data import rotation,visible,SCALE,scene_targets

def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def main():
    planfile=W/'protocol/train05_english.json';plan=read(planfile);reg=read(W/'protocol/train05_data_registration.json')
    assert sha(planfile)==reg['plan_sha256']
    assert sha(W/'protocol/train05_training_frames.json')==reg['frames_sha256']
    addendum=read(W/'protocol/train05_state_pair_addendum.json');assert addendum['plan_sha256']==reg['plan_sha256']
    source=W/'data/dataset04_en';out=W/'data/dataset05_en';assert not out.exists()
    assert sha(source/'audit.json')==plan['data_generation']['base_dataset_audit_sha256']
    for f,h in read(source/'audit.json')['files'].items():assert sha(source/f)==h,f
    teacher=source/'teacher_source.py';assert sha(teacher)==plan['data_generation']['teacher_source_sha256']
    ns=dict(np=np,math=math,rotation=rotation,SCALE=SCALE,__name__='teacher_snapshot');exec(compile(teacher.read_text(encoding='utf8'),str(teacher),'exec'),ns);teach=ns['teacher_chunk']
    original=read(W/'protocol/plan.json');frames=read(W/'protocol/training_frames.json')
    retained=read(P/'outputs/vla_data_realism_precision_02/poses.json')['frames'];extra=read(W/'protocol/train05_training_frames.json')
    assert len(frames)==4000 and len(retained)==2408 and len(extra)==2000
    assert all((W/'data/rendered05_png'/f'{i:05d}.png').is_file() for i in range(2000))
    allposes=frames+retained+extra;target=[]
    for f in frames:
        pos=np.asarray(original['train_layouts'][f['layout']]['positions']);target.append(dict(blue=pos[f['blue_actor']],red=pos[1-f['blue_actor']]))
    target.extend([scene_targets(W/'scenes/primitive_regression/physics/rescue_scene.xml')]*len(retained))
    for f in extra:
        pos=np.asarray(original['train_layouts'][f['layout']]['positions']);target.append(dict(blue=pos[f['blue_actor']],red=pos[1-f['blue_actor']]))
    with np.load(source/'audited_samples.npz') as a:base={k:a[k].copy() for k in a.files}
    with np.load(source/'sampling_metadata.npz') as a:oldmeta={k:a[k].copy() for k in a.files}
    assert len(base['task'])==73712
    out.mkdir();(out/'images').mkdir();sources=[]
    oldhashes=read(W/'data/dataset/image_checksums.json')
    for i in range(6408):
        p=W/'data/dataset/images'/f'{i:05d}.jpg';assert sha(p)==oldhashes[p.name]
        sources.append(dict(id=i,path=p.relative_to(W).as_posix(),sha256=oldhashes[p.name],domain=0 if i<4000 else 1))
    for j in range(2000):
        i=6408+j;p=out/'images'/f'{i:05d}.jpg'
        Image.open(W/'data/rendered05_png'/f'{j:05d}.png').convert('RGB').save(p,quality=70)
        sources.append(dict(id=i,path=p.relative_to(W).as_posix(),sha256=sha(p),domain=2))
    ids=[];tasks=[];states=[];labels=[];nav={};pairs=[]
    def add(i,t,s):
        idx=len(base['task'])+len(tasks);ids.append(i);tasks.append(t);states.append(s.copy());labels.append(teach(t,np.asarray(allposes[i]['qpos']),s,target[i]));return idx
    for i in range(6408,8408):
        f=allposes[i];q=np.asarray(f['qpos']);s=np.asarray(f['state'],dtype=np.float32);nav[i]=[]
        for t,c in enumerate(['blue','red']):nav[i].append(add(i,t,s) if visible(q,target[i][c]) else -1)
    quartets=np.load(source/'quartets.npy').tolist();oldquartets=len(quartets)
    for i in range(6408,8408,2):
        if min(nav[i]+nav[i+1])>=0:quartets.append(nav[i]+nav[i+1])
    rng=np.random.default_rng(plan['data_generation']['own_velocity_pairing']['state_seed'])
    for i,f in enumerate(allposes):
        if f['state'][8]<=.5:continue
        for t in range(2,7):
            s=np.asarray(f['state'],dtype=np.float32).copy()
            if t in [4,5]:
                s[6]=(1 if t==4 else -1)*rng.uniform(-.2,math.pi/2+.25);s[7]=rng.uniform(-.35,.35)
            u=rng.random();r=0 if u<.2 else rng.uniform(.02,.12) if u<.7 else rng.uniform(.12,.35)
            theta=rng.uniform(-math.pi,math.pi);s[:2]=[r*math.cos(theta),r*math.sin(theta)]
            first=add(i,t,s);s[:2]*=-1;second=add(i,t,s);pairs.append([first,second])
    arrays=dict(image=np.r_[base['image'],np.asarray(ids,dtype=np.int32)],task=np.r_[base['task'],np.asarray(tasks,dtype=np.int16)],state=np.concatenate([base['state'],np.asarray(states,dtype=np.float32)]),action=np.concatenate([base['action'],np.asarray(labels,dtype=np.float32)]))
    for k in base:assert np.array_equal(arrays[k][:len(base['task'])],base[k]),k
    for a,b,c,d in quartets:
        assert np.array_equal(arrays['state'][a],arrays['state'][d])
        assert np.array_equal(arrays['action'][a],arrays['action'][d]) and np.array_equal(arrays['action'][b],arrays['action'][c])
    pp=np.asarray(pairs,dtype=np.int32);a,b=pp.T
    assert np.array_equal(arrays['image'][a],arrays['image'][b]) and np.array_equal(arrays['task'][a],arrays['task'][b])
    assert np.array_equal(arrays['state'][a,2:],arrays['state'][b,2:]) and np.array_equal(arrays['state'][a,:2],-arrays['state'][b,:2])
    assert np.array_equal(arrays['action'][a,:,2:],arrays['action'][b,:,2:])
    assert np.array_equal(arrays['action'][a,:,:2],-arrays['action'][b,:,:2])
    assert np.isfinite(arrays['state']).all() and np.isfinite(arrays['action']).all() and np.abs(arrays['action']).max()<=1.0001
    domain=np.asarray([sources[i]['domain'] for i in arrays['image']],dtype=np.int8)
    distance=np.full(len(tasks),np.nan,dtype=np.float32)
    for k,(i,t) in enumerate(zip(ids,tasks)):
        if t<2:distance[k]=np.linalg.norm(target[i][['blue','red'][t]][:2]+[-.9,0]-np.asarray(allposes[i]['qpos'])[:2])
    distance=np.r_[oldmeta['goal_distance'],distance]
    np.savez_compressed(out/'audited_samples.npz',**arrays)
    np.save(out/'quartets.npy',np.asarray(quartets,dtype=np.int32));np.save(out/'state_pairs.npy',pp)
    np.savez_compressed(out/'sampling_metadata.npz',domain=domain,goal_distance=distance)
    write(out/'image_sources.json',sources);shutil.copy2(teacher,out/'teacher_source.py')
    previous=read(source/'manifest.json')
    manifest=dict(prompts=previous['prompts'],prompt_variants=previous['prompt_variants'],samples=len(arrays['task']),quartets=len(quartets),original_quartets=oldquartets,state_pairs=len(pairs),new_images=6000,retention_images=2408,total_images=8408,original_sample_count=73712,additional_images=2000,additional_state_examples=len(pairs)*2,additional_navigation_examples=len(tasks)-len(pairs)*2,existing_pixels_changed=False,existing_labels_unchanged=True,image_sources='image_sources.json',training_plan_sha256=sha(planfile),source_dataset_audit_sha256=sha(source/'audit.json'),teacher_source_sha256=sha(out/'teacher_source.py'),teacher_standoff_m=1.0,scoring_standoff_m=.9,braking_coefficient=.8,geometry_not_model_input=True,previous_dataset_manifest=previous)
    write(out/'manifest.json',manifest)
    write(out/'audit.json',dict(files={p.name:sha(p) for p in out.iterdir() if p.is_file()},plan_sha256=sha(planfile),addendum_sha256=sha(W/'protocol/train05_state_pair_addendum.json'),inputs=['image','task','state'],target='action',image_domains=[int(sum(s['domain']==d for s in sources)) for d in range(3)],teacher_geometry_in_model_npz=False,evaluation_inputs_used_for_training=0,existing_labels_byte_identical=True,opposite_state_pairs_verified=True,all_counterfactual_labels_swapped_exactly=True))
    print(json.dumps(dict(samples=len(arrays['task']),quartets=len(quartets),pairs=len(pairs),images=len(sources))),flush=True)
if __name__=='__main__':main()
