"""Relabel audited training inputs only; preserve all input arrays and images."""
import hashlib,json,shutil,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent;sys.path.insert(0,str(P))
from make_revision_data import rotation,SCALE,scene_targets
from teacher_flight13 import teacher_chunk as oldteacher
from teacher_flight14 import teacher_chunk as teacher,BRAKING_COEFFICIENT,NAVIGATION_LOOKAHEAD_S
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf8')
def main():
    planfile=W/'protocol/train14_english.json';plan=read(planfile)
    source=W/'data/dataset13_en';out=W/'data/dataset14_en';assert not out.exists()
    assert sha(source/'audit.json')==plan['data']['source_audit_sha256']
    assert sha(W/'scripts/teacher_flight14.py')==plan['teacher_source_sha256']
    for f,h in read(source/'audit.json')['files'].items():assert sha(source/f)==h,f
    original=read(W/'protocol/plan.json');frames=read(W/'protocol/training_frames.json')
    retained=read(P/'outputs/vla_data_realism_precision_02/poses.json')['frames']
    extra=read(W/'protocol/train05_training_frames.json');poses=frames+retained+extra;targets=[]
    for f in frames:
        pos=np.asarray(original['train_layouts'][f['layout']]['positions'])
        targets.append(dict(blue=pos[f['blue_actor']],red=pos[1-f['blue_actor']]))
    targets.extend([scene_targets(W/'scenes/primitive_regression/physics/rescue_scene.xml')]*len(retained))
    for f in extra:
        pos=np.asarray(original['train_layouts'][f['layout']]['positions'])
        targets.append(dict(blue=pos[f['blue_actor']],red=pos[1-f['blue_actor']]))
    sources=read(source/'image_sources.json');assert len(sources)==len(poses)==len(targets)==8408
    for row in sources:assert sha(W/row['path'])==row['sha256']
    with np.load(source/'audited_samples.npz') as d:base={k:d[k].copy() for k in d.files}
    inputs={k:hashlib.sha256(base[k].tobytes()).hexdigest() for k in ['image','task','state']}
    old=base['action'].copy();nav=np.flatnonzero(base['task']<2);maximum=0.
    for count,k in enumerate(nav):
        i=int(base['image'][k]);t=int(base['task'][k]);s=base['state'][k];q=np.asarray(poses[i]['qpos'])
        reconstructed=oldteacher(t,q,s,targets[i],rotation,SCALE)
        diff=float(np.max(np.abs(reconstructed-old[k])));maximum=max(maximum,diff);assert diff<1e-5,(k,diff)
        new=teacher(t,q,s,targets[i],rotation,SCALE)
        assert np.array_equal(new[:,[2,4,5]],old[k,:][:,[2,4,5]])
        base['action'][k]=new
        if count%5000==0:print(json.dumps(dict(navigation=count,total=len(nav))),flush=True)
    hold=np.flatnonzero(np.isin(base['task'],[2,4,5,6]))
    s=base['state'][hold];t=base['task'][hold]
    valid=(s[:,8]>.5)&~((t==2)&(s[:,3]<.25))
    def brakes(coefficient):
        b=-coefficient*s[:,:2].astype(float);b[~valid]=0
        b*=np.minimum(1.,.2/np.maximum(np.linalg.norm(b,axis=1,keepdims=True),1e-12))
        return (b/np.asarray(SCALE[:2])).astype(np.float32)
    expected=brakes(1.2)
    assert np.allclose(old[hold,:,:2],expected[:,None,:],rtol=0,atol=1e-6)
    base['action'][hold,:,:2]=brakes(BRAKING_COEFFICIENT)[:,None,:]
    assert np.array_equal(base['action'][base['task']==3],old[base['task']==3])
    assert np.array_equal(base['action'][hold,:,3],old[hold,:,3])
    assert np.array_equal(base['action'][:,:,[2,4,5]],old[:,:,[2,4,5]])
    assert all(hashlib.sha256(base[k].tobytes()).hexdigest()==h for k,h in inputs.items())
    for a,b,c,d in np.load(source/'quartets.npy'):
        assert np.array_equal(base['action'][a],base['action'][d]) and np.array_equal(base['action'][b],base['action'][c])
    assert np.isfinite(base['action']).all()
    assert np.max(np.linalg.norm(base['action'][:,:,:2]*SCALE[:2],axis=-1))<=.200001
    assert np.max(np.abs(base['action'][nav,:,3]*SCALE[3]))<=.250001
    out.mkdir();np.savez_compressed(out/'audited_samples.npz',**base)
    for name in ['quartets.npy','state_pairs.npy','state_quartets.npy','image_sources.json','sampling_metadata.npz']:shutil.copy2(source/name,out/name)
    shutil.copy2(W/'scripts/teacher_flight14.py',out/'teacher_source.py')
    m=read(source/'manifest.json');m.update(braking_coefficient=BRAKING_COEFFICIENT,navigation_lookahead_s=NAVIGATION_LOOKAHEAD_S,
        navigation_heading_rule='Forecast target bearing1s ahead using current own linear/angular velocity; same translation law and world goal.',
        training_plan_sha256=sha(planfile),source_dataset_audit_sha256=sha(source/'audit.json'),teacher_source_sha256=sha(out/'teacher_source.py'),added_images=0,added_state_examples=0)
    write(out/'manifest.json',m)
    write(out/'audit.json',dict(files={p.name:sha(p) for p in out.iterdir() if p.is_file()},plan_sha256=sha(planfile),
        inputs=['image','task','state'],target='action',input_arrays_sha256=inputs,
        images_unchanged=True,states_unchanged=True,prompts_unchanged=True,
        landing_labels_byte_identical=True,primitive_yaw_byte_identical=True,vertical_and_requests_byte_identical=True,
        relabeled_navigation_examples=len(nav),relabeled_stationary_examples=len(hold),source_teacher_max_reconstruction_error=maximum,
        all_counterfactual_labels_swapped_exactly=True,evaluation_images_or_states_used_for_training=0,teacher_geometry_in_model_npz=False))
    print(json.dumps(dict(samples=len(base['task']),navigation=len(nav),stationary=len(hold),images=len(sources),audit_sha256=sha(out/'audit.json'))))
if __name__=='__main__':main()
