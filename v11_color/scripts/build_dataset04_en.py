"""Relabel captured-state braking after a separate train04 preregistration.

No new pixels, geometry, or evaluation records are used as training examples.
Navigation, landing, yaw, altitude and request labels remain byte-identical.
"""
import hashlib,json,shutil
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    planfile=W/'protocol/train04_english.json';plan=read(planfile)
    source=W/'data/dataset03';out=W/'data/dataset04_en'
    assert not out.exists()
    assert sha(source/'audit.json')==plan['training']['source_dataset_audit_sha256']
    proposal=W/'scripts/teacher_braking_proposal.py'
    assert sha(proposal)==plan['training']['braking_proposal_sha256']
    coefficient=plan['training']['braking_coefficient'];assert coefficient==.8
    for f,h in read(source/'audit.json')['files'].items():assert sha(source/f)==h
    with np.load(source/'audited_samples.npz') as a:arrays={k:a[k].copy() for k in a.files}
    original=arrays['action'].copy()
    eligible=np.isin(arrays['task'],[2,4,5,6])&(arrays['state'][:,8]>.5)
    braking=-coefficient*arrays['state'][eligible,:2].astype(np.float64)
    braking*=np.minimum(1.,.2/np.maximum(np.linalg.norm(braking,axis=1,keepdims=True),1e-12))
    arrays['action'][eligible,:,:2]=braking[:,None,:]/.2
    assert np.array_equal(arrays['action'][~eligible],original[~eligible])
    assert np.array_equal(arrays['action'][:,:,2:],original[:,:,2:])
    assert np.max(np.linalg.norm(arrays['action'][eligible,:,:2]*.2,axis=2))<=.200001
    assert np.isfinite(arrays['action']).all()
    out.mkdir(exist_ok=False)
    np.savez_compressed(out/'audited_samples.npz',**arrays)
    for name in ['quartets.npy','sampling_metadata.npz']:shutil.copy2(source/name,out/name)
    baseline=(source/'teacher_source.py').read_text(encoding='utf-8').replace('def teacher_chunk(', 'def baseline_teacher_chunk(',1)
    # Preserve the actual teacher implementation used for this new label set.
    proposal_source=proposal.read_text(encoding='utf-8').split("if __name__=='__main__':")[0]
    teacher=baseline+'\n'+proposal_source+'\nteacher_chunk=make_teacher(baseline_teacher_chunk,SCALE,coefficient=.8)\n'
    (out/'teacher_source.py').write_text(teacher,encoding='utf-8')
    manifest=read(source/'manifest.json');manifest.update(training_plan_sha256=sha(planfile),
        source_dataset_audit_sha256=sha(source/'audit.json'),teacher_source_sha256=sha(out/'teacher_source.py'),
        braking_coefficient=coefficient,braking_tasks=[2,4,5,6],braking_examples=int(eligible.sum()),
        braking_scope='Captured onboard estimated horizontal velocity, constant across the predicted chunk; no runtime controller change',
        pixels_changed=False,additional_images=0,additional_state_examples=0)
    write(out/'manifest.json',manifest)
    write(out/'audit.json',dict(files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        plan_sha256=sha(planfile),image_checksums_source='../dataset/image_checksums.json',
        navigation_labels_unchanged=True,landing_labels_unchanged=True,non_horizontal_labels_unchanged=True,
        unarmed_labels_unchanged=True,inputs=['image','task','state'],target='action',
        evaluation_images_or_states_used_for_training=0,
        note='Teacher design was informed by failed evaluation round 1. Those conditions are no longer an untouched final test. A separate round 2 must be preregistered before training.'))
    print(json.dumps(dict(samples=len(arrays['task']),relabeled=int(eligible.sum()),plan_sha256=sha(planfile))))
if __name__=='__main__':main()
