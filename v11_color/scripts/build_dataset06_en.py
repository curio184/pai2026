"""Registered train06 relabeling and state anchors; no new images or evaluation input."""
import hashlib,json,math,shutil,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent;sys.path.insert(0,str(P))
from make_revision_data import rotation,SCALE,scene_targets
from teacher_flight06 import teacher_chunk as teacher06
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    planfile=W/'protocol/train06_english.json';plan=read(planfile)
    source=W/'data/dataset05_en';out=W/'data/dataset06_en';assert not out.exists()
    assert sha(source/'audit.json')==plan['data']['source_audit_sha256']
    assert sha(W/'scripts/teacher_flight06.py')==plan['teacher_source_sha256']
    for f,h in read(source/'audit.json')['files'].items():assert sha(source/f)==h,f
    oldteacherfile=source/'teacher_source.py'
    ns=dict(np=np,math=math,rotation=rotation,SCALE=SCALE,__name__='teacher_snapshot')
    exec(compile(oldteacherfile.read_text(encoding='utf8'),str(oldteacherfile),'exec'),ns)
    original=read(W/'protocol/plan.json')
    frames=read(W/'protocol/training_frames.json');retained=read(P/'outputs/vla_data_realism_precision_02/poses.json')['frames']
    extra=read(W/'protocol/train05_training_frames.json');poses=frames+retained+extra
    target=[]
    for f in frames:
        pos=np.asarray(original['train_layouts'][f['layout']]['positions']);target.append(dict(blue=pos[f['blue_actor']],red=pos[1-f['blue_actor']]))
    target.extend([scene_targets(W/'scenes/primitive_regression/physics/rescue_scene.xml')]*len(retained))
    for f in extra:
        pos=np.asarray(original['train_layouts'][f['layout']]['positions']);target.append(dict(blue=pos[f['blue_actor']],red=pos[1-f['blue_actor']]))
    sources=read(source/'image_sources.json');assert len(sources)==len(poses)==8408
    for row in sources:assert sha(W/row['path'])==row['sha256']
    with np.load(source/'audited_samples.npz') as d:base={k:d[k].copy() for k in d.files}
    with np.load(source/'sampling_metadata.npz') as d:meta={k:d[k].copy() for k in d.files}
    oldactions=base['action'].copy();maximum_reconstruction_difference=0.
    nav=np.flatnonzero(base['task']<2)
    for counter,k in enumerate(nav):
        i=int(base['image'][k]);t=int(base['task'][k]);s=base['state'][k];q=np.asarray(poses[i]['qpos'])
        reconstructed=ns['teacher_chunk'](t,q,s,target[i])
        delta=float(np.abs(reconstructed-oldactions[k]).max());maximum_reconstruction_difference=max(maximum_reconstruction_difference,delta)
        assert delta<1e-5,('Source teacher reconstruction mismatch',int(k),delta)
        new=teacher06(t,q,s,target[i],rotation,SCALE)
        assert np.array_equal(new[:,2:],oldactions[k,:,2:]),('Nonhorizontal label changed',int(k))
        base['action'][k,:,:2]=new[:,:2]
        if counter%5000==0:print(json.dumps(dict(relabelled_navigation=counter,total=len(nav))),flush=True)
    def horizontal_labels(tasks,states,actions):
        eligible=np.isin(tasks,[2,4,5,6])&(states[:,8]>.5)
        brake=-1.2*states[eligible,:2].astype(np.float64)
        ground=(tasks[eligible]==2)&(states[eligible,3]<.25);brake[ground]=0
        brake*=np.minimum(1.,.2/np.maximum(np.linalg.norm(brake,axis=1,keepdims=True),1e-12))
        actions[eligible,:,:2]=brake[:,None,:]/SCALE[:2]
    horizontal_labels(base['task'],base['state'],base['action'])
    assert np.array_equal(base['action'][:,:,2:],oldactions[:,:,2:])
    pairs=np.load(source/'state_pairs.npy');assert pairs.shape==(40060,2)
    first=pairs[:,0]
    new_image=np.repeat(base['image'][first],2);new_task=np.repeat(base['task'][first],2)
    new_state=np.repeat(base['state'][first],2,axis=0);new_action=np.repeat(base['action'][first],2,axis=0)
    new_state[::2,:2]=0;new_state[1::2,:2]*=.5
    horizontal_labels(new_task,new_state,new_action)
    start=len(base['task']);indices=np.arange(start,start+len(new_task),dtype=np.int32).reshape(-1,2)
    state_quartets=np.column_stack([pairs,indices])
    arrays=dict(image=np.r_[base['image'],new_image],task=np.r_[base['task'],new_task],
        state=np.concatenate([base['state'],new_state]),action=np.concatenate([base['action'],new_action]))
    assert len(arrays['task'])==plan['data']['expected_total_examples']
    color_quartets=np.load(source/'quartets.npy')
    for a,b,c,d in color_quartets:
        assert np.array_equal(arrays['action'][a],arrays['action'][d]) and np.array_equal(arrays['action'][b],arrays['action'][c])
    a,b,c,d=state_quartets.T
    for indices in [b,c,d]:
        assert np.array_equal(arrays['image'][a],arrays['image'][indices]) and np.array_equal(arrays['task'][a],arrays['task'][indices])
        assert np.array_equal(arrays['state'][a,2:],arrays['state'][indices,2:])
        assert np.array_equal(arrays['action'][a,:,2:],arrays['action'][indices,:,2:])
    assert np.array_equal(arrays['state'][a,:2],-arrays['state'][b,:2])
    assert np.count_nonzero(arrays['state'][c,:2])==0
    assert np.array_equal(arrays['state'][d,:2],arrays['state'][a,:2]*.5)
    assert np.count_nonzero(arrays['action'][c,:,:2])==0
    assert np.array_equal(arrays['action'][a,:,:2],-arrays['action'][b,:,:2])
    assert np.isfinite(arrays['state']).all() and np.isfinite(arrays['action']).all()
    assert np.linalg.norm(arrays['action'][:,:,:2]*SCALE[:2],axis=2).max()<=.200001
    out.mkdir();np.savez_compressed(out/'audited_samples.npz',**arrays)
    np.save(out/'state_quartets.npy',state_quartets)
    for name in ['quartets.npy','state_pairs.npy','image_sources.json']:shutil.copy2(source/name,out/name)
    np.savez_compressed(out/'sampling_metadata.npz',domain=np.r_[meta['domain'],np.repeat(meta['domain'][first],2)],
        goal_distance=np.r_[meta['goal_distance'],np.repeat(meta['goal_distance'][first],2)])
    shutil.copy2(W/'scripts/teacher_flight06.py',out/'teacher_source.py')
    manifest=read(source/'manifest.json');manifest.update(samples=len(arrays['task']),state_quartets=len(state_quartets),
        additional_images=0,additional_state_examples=len(new_task),existing_labels_unchanged=False,nonhorizontal_labels_unchanged=True,
        braking_coefficient=1.2,navigation_velocity_damping=.5,grounded_takeoff_horizontal_zero_below_m=.25,
        training_plan_sha256=sha(planfile),source_dataset_audit_sha256=sha(source/'audit.json'),
        teacher_source_sha256=sha(out/'teacher_source.py'))
    write(out/'manifest.json',manifest)
    write(out/'audit.json',dict(files={p.name:sha(p) for p in out.iterdir() if p.is_file()},plan_sha256=sha(planfile),
        source_teacher_max_reconstruction_error=maximum_reconstruction_difference,inputs=['image','task','state'],target='action',
        evaluation_images_or_states_used_for_training=0,images_unchanged=True,nonhorizontal_existing_labels_byte_identical=True,
        all_counterfactual_labels_swapped_exactly=True,state_calibration_quartets_verified=True,teacher_geometry_in_model_npz=False))
    print(json.dumps(dict(samples=len(arrays['task']),navigation=len(nav),state_quartets=len(state_quartets),images=len(sources),audit_sha256=sha(out/'audit.json'))))
if __name__=='__main__':main()
