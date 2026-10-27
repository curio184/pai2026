"""Teach visual position corrections inside the scoring radius, not edge stops.

Retain previous rendered images and add exact recorded inputs from both final-
model checks. Only teacher labels use scene coordinates; runtime remains RGB,
language and own estimated state. All previous data/weights/runs are preserved.
"""
from pathlib import Path
import json,hashlib,shutil,time,inspect
import numpy as np
from PIL import Image
from make_revision_data import teacher_chunk,visible,scene_targets,sha
ROOT=Path(__file__).resolve().parent
for record_name in ['realism_trained_01','realism_confirmed_02']:
    result=ROOT/'outputs/ardupilot'/record_name/'result.json';start=time.monotonic()
    while not result.exists():
        if time.monotonic()-start>900:raise TimeoutError(record_name)
        time.sleep(5)
out=ROOT/'outputs/vla_data_realism_precision_02';out.mkdir(exist_ok=False);(out/'images').mkdir()
original=ROOT/'outputs/vla_data_realism_01';metadata=json.loads((original/'poses.json').read_text());frames=metadata['frames'];sources=metadata['sources']
for i,frame in enumerate(frames):shutil.copy2(original/'images'/f'{i:05d}.jpg',out/'images'/f'{i:05d}.jpg')
for record_name in ['realism_trained_01','realism_confirmed_02']:
    record=ROOT/'outputs/ardupilot'/record_name
    for profile in ['blue','red','turns','left']:
        case=record/profile;rows=[json.loads(s) for s in (case/'trace.jsonl').read_text().splitlines()];times=np.asarray([r['t'] for r in rows])
        events=json.loads((case/'vla_link_events.json').read_text())
        for event in events:
            if event.get('event')!='inference':continue
            file=case/'observations'/event['image_file'];assert sha(file)==event['image_sha256']
            j=max(0,int(np.searchsorted(times,event['sim_time_capture'],side='right')-1));i=len(frames)
            frames.append(dict(qpos=rows[j]['truth'][19:26],state=event['estimated_state'],origin=record_name+'/'+profile))
            shutil.copy2(file,out/'images'/f'{i:05d}.jpg')
        sources.append(dict(record=record_name,profile=profile,trace_sha256=sha(case/'trace.jsonl'),exact_recorded_jpegs=True))
# This is a teacher change only. The independent physical scorer stays at 25cm.
teacher_source=inspect.getsource(teacher_chunk).replace('np.linalg.norm(delta)>.25','np.linalg.norm(delta)>.04')
teacher_source=teacher_source.replace('# Teach a true zero-velocity stop within the original task\n                # tolerance, rather than noisy micromotion around an exact point.','# Continue visual correction within the scoring tolerance.\n                # Use only a 4cm central deadband, leaving room for drift.')
from make_revision_data import rotation,SCALE
namespace=dict(np=np,math=__import__('math'),rotation=rotation,SCALE=SCALE)
exec(teacher_source,namespace);precise_teacher=namespace['teacher_chunk']
(out/'teacher_source.py').write_text(teacher_source,encoding='utf8')
targets=scene_targets(ROOT/'assets/civic_realism/physics03/rescue_scene.xml')
rng=np.random.default_rng(20261027);images=[];tasks=[];states=[];labels=[];poses=[];pairs=[];hashes={}
def add(i,task,p,s):
    j=len(tasks);images.append(i);tasks.append(task);states.append(s.copy());labels.append(precise_teacher(task,p,s,targets));poses.append(p);return j
for i,frame in enumerate(frames):
    file=out/'images'/f'{i:05d}.jpg'
    with Image.open(file) as im:assert im.size==(320,240)
    hashes[file.name]=sha(file);p=np.asarray(frame['qpos'],float);s=np.asarray(frame['state'],np.float32);s[6]=0
    nav=[add(i,task,p,s) if s[3]<=.8 or visible(p,targets[color]) else None for task,color in enumerate(['blue','red'])]
    if all(j is not None for j in nav) and s[3]>.8:pairs.append(nav)
    for task in range(2,7):
        own=s.copy()
        if task in [4,5] and s[3]>.8:own[6]=(1 if task==4 else -1)*rng.uniform(-.2,np.pi/2+.25);own[7]=rng.uniform(-.35,.35)
        add(i,task,p,own)
        if task in [4,5] and s[3]>.8:
            own=s.copy();own[6]=(np.pi/2 if task==4 else -np.pi/2)+rng.uniform(-.12,.12);own[7]=rng.uniform(-.08,.08);add(i,task,p,own)
arrays=dict(image=np.asarray(images,np.int32),task=np.asarray(tasks,np.int16),state=np.asarray(states,np.float32),action=np.asarray(labels,np.float32),teacher_qpos=np.asarray(poses,np.float32))
assert all(np.isfinite(v).all() for v in arrays.values());assert arrays['action'].shape[1:]==(32,6)
np.savez_compressed(out/'audited_samples.npz',**arrays);np.save(out/'nav_pairs.npy',np.asarray(pairs,np.int32))
(out/'image_checksums.json').write_text(json.dumps(hashes,separators=(',',':')))
(out/'poses.json').write_text(json.dumps(dict(frames=frames,sources=sources),separators=(',',':')))
manifest=json.loads((original/'manifest.json').read_text(encoding='utf8'));manifest.update(images=len(frames),samples=len(tasks),paired_nav_examples=len(pairs),recorded_pose_sources=sources,teacher_stop_deadband_m=.04,scoring_goal_tolerance_m=.25,optical_scene_note='Original revision02 synthetic images plus exact revision03 flight observations. Both provenances retained.',teacher_source_sha256=sha(out/'teacher_source.py'))
(out/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
audit=dict(all_tasks_present=bool((np.bincount(arrays['task'],minlength=7)>0).all()),task_counts=np.bincount(arrays['task'],minlength=7).tolist(),sha256=sha(out/'audited_samples.npz'),image_manifest_sha256=sha(out/'image_checksums.json'),nav_pairs_sha256=sha(out/'nav_pairs.npy'),images_hashed=len(hashes),kept_samples=len(tasks),paired_examples=len(pairs),teacher_geometry_is_model_input=False)
(out/'audit.json').write_text(json.dumps(audit,indent=2))
plan=json.loads((ROOT/'finetune_plan_realism_01.json').read_text())
checkpoint=ROOT/'outputs/smolvla_training_realism_01/final'
plan.update(initial_checkpoint=checkpoint.relative_to(ROOT).as_posix(),initial_checkpoint_sha256=sha(checkpoint/'model.safetensors'),dataset=out.relative_to(ROOT).as_posix(),output='outputs/smolvla_training_realism_precision_02',steps=4000,seed=20261027,rationale='Observed near-zero VLA requests still leave approximately 5 cm/s physical drift. A 25 cm teacher deadband stopped correction at the scoring edge. Train continuous visual correction to a 4 cm deadband, using exact failed-run images as well as previous supervision. No evaluation threshold or runtime target oracle change.')
(ROOT/'finetune_plan_realism_precision_02.json').write_text(json.dumps(plan,indent=2))
progress=ROOT/'flight_progress.py';before=sha(progress);text=progress.read_text();assert 'hold_s=4.0, command_limit_m_s=.035' in text
progress.write_text(text.replace('hold_s=4.0, command_limit_m_s=.035','hold_s=4.0, command_limit_m_s=.065'),encoding='utf8')
revision=dict(reason=plan['rationale'],training_plan='finetune_plan_realism_precision_02.json',data_audit=audit,own_state_dwell_s=4.0,small_model_correction_limit_m_s=.065,physical_success_criteria_changed=False,runtime_target_coordinates_added=False,previous_model_sha256=plan['initial_checkpoint_sha256'],progress_source_before_sha256=before,progress_source_after_sha256=sha(progress),preserved_failed_collections=['realism_trained_01','realism_confirmed_02'])
(ROOT/'realism_precision_revision.json').write_text(json.dumps(revision,indent=2))
print(json.dumps(audit),flush=True)
