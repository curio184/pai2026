"""Supervision for the frozen room; scene geometry is labels only, never input."""
import argparse,json,math,hashlib,time
from pathlib import Path
import numpy as np
from PIL import Image
from make_revision_data import quaternion,teacher_chunk,visible,scene_targets,sha
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs/vla_data_civic_01'

def prepare():
    OUT.mkdir(exist_ok=False);(OUT/'images').mkdir()
    rng=np.random.default_rng(20261026);frames=[]
    targets=scene_targets(ROOT/'assets/civic_world/physics/rescue_scene.xml')
    for i in range(1600):
        if i<700:
            x=rng.uniform(-.2,2.65);y=rng.uniform(-1.1,1.1);z=rng.uniform(.87,1.15);yaw=rng.uniform(-.15,.15);armed=1
        elif i<1200:
            target=targets['blue' if i%2==0 else 'red']+[-.9,0,0]
            x=target[0]+rng.uniform(-.52,.33);y=target[1]+rng.uniform(-.45,.45);z=rng.uniform(.88,1.12);yaw=rng.uniform(-.16,.16);armed=1
        else:
            x=rng.uniform(-.1,2.5);y=rng.uniform(-1,1);z=.033 if i%5==0 else rng.uniform(.06,1.3);yaw=rng.uniform(-1.9,1.9);armed=int(z>.05)
        roll=rng.uniform(-.06,.06) if armed else 0;pitch=rng.uniform(-.06,.06) if armed else 0
        pose=[x,y,z,*quaternion(roll,pitch,yaw)]
        state=[rng.uniform(-.18,.18)*armed,rng.uniform(-.12,.12)*armed,rng.uniform(-.07,.07)*armed,z,roll,-pitch,0,rng.uniform(-.05,.05)*armed,armed]
        frames.append(dict(qpos=pose,state=state,origin='sampled'))
    origins=[]
    for record_name in ['inference_revision_04','civic_baseline_01']:
        record=ROOT/'outputs/ardupilot'/record_name
        if not (record/'result.json').exists():continue
        for profile in ['blue','red','turns','left']:
            case=record/profile
            rows=[json.loads(s) for s in (case/'trace.jsonl').read_text().splitlines()]
            events=json.loads((case/'vla_link_events.json').read_text())
            times=np.array([row['t'] for row in rows]);observations=[e for e in events if e.get('event')=='inference']
            for e in observations[::2]:
                j=max(0,int(np.searchsorted(times,e['sim_time_capture'],side='right')-1))
                frames.append(dict(qpos=rows[j]['truth'][19:26],state=e['estimated_state'],origin=f'{record_name}/{profile}'))
            origins.append(dict(record=record_name,profile=profile,trace_sha256=sha(case/'trace.jsonl')))
    (OUT/'poses.json').write_text(json.dumps(dict(seed=20261026,frames=frames,sources=origins),separators=(',',':')))
    print('PREPARED',len(frames),flush=True)

def render():
    from civic_camera import LiveCamera
    frames=json.loads((OUT/'poses.json').read_text())['frames']
    camera=LiveCamera(ROOT/'assets/civic_world/physics/rescue_scene.xml')
    started=time.monotonic()
    for i,frame in enumerate(frames):
        file=OUT/'images'/f'{i:05d}.jpg'
        if file.exists():raise FileExistsError('Do not overwrite rendered evidence')
        rgb=camera.render(frame['qpos']);Image.fromarray(rgb).save(file,format='JPEG',quality=70)
        if i%100==0:print(json.dumps(dict(images=i+1,total=len(frames),elapsed_s=time.monotonic()-started)),flush=True)
    camera.close()
    (OUT/'render_result.json').write_text(json.dumps(dict(images=len(frames),elapsed_s=time.monotonic()-started,provenance=camera.provenance),indent=2))

def finalize():
    metadata=json.loads((OUT/'poses.json').read_text());frames=metadata['frames']
    rendered=json.loads((OUT/'render_result.json').read_text());assert rendered['images']==len(frames)
    targets=scene_targets(ROOT/'assets/civic_world/physics/rescue_scene.xml')
    rng=np.random.default_rng(20261026);images=[];tasks=[];states=[];labels=[];poses=[];pairs=[];hashes={}
    def add(i,task,p,s):
        j=len(tasks);images.append(i);tasks.append(task);states.append(s.copy());labels.append(teacher_chunk(task,p,s,targets));poses.append(p);return j
    for i,frame in enumerate(frames):
        file=OUT/'images'/f'{i:05d}.jpg'
        with Image.open(file) as img:assert img.size==(320,240)
        hashes[file.name]=sha(file)
        p=np.array(frame['qpos'],float);s=np.array(frame['state'],dtype=np.float32);s[6]=0
        nav=[add(i,task,p,s) if s[3]<=.8 or visible(p,targets[color]) else None for task,color in enumerate(['blue','red'])]
        if all(j is not None for j in nav) and s[3]>.8:pairs.append(nav)
        for task in range(2,7):
            own=s.copy()
            if task in [4,5] and s[3]>.8:
                own[6]=(1 if task==4 else -1)*rng.uniform(-.2,math.pi/2+.25);own[7]=rng.uniform(-.35,.35)
            add(i,task,p,own)
            if task in [4,5] and s[3]>.8:
                own=s.copy();own[6]=(math.pi/2 if task==4 else -math.pi/2)+rng.uniform(-.12,.12);own[7]=rng.uniform(-.08,.08);add(i,task,p,own)
    arrays=dict(image=np.array(images,np.int32),task=np.array(tasks,np.int16),state=np.array(states,np.float32),action=np.array(labels,np.float32),teacher_qpos=np.array(poses,np.float32))
    assert all(np.isfinite(v).all() for v in arrays.values())
    assert arrays['action'].shape[1:]==(32,6) and np.abs(arrays['action']).max()<=1.0001
    for a,b in pairs:assert images[a]==images[b] and np.array_equal(states[a],states[b]) and tasks[a]==0 and tasks[b]==1
    np.savez_compressed(OUT/'audited_samples.npz',**arrays);np.save(OUT/'nav_pairs.npy',np.array(pairs,np.int32))
    (OUT/'image_checksums.json').write_text(json.dumps(hashes,separators=(',',':')))
    prompts=json.loads((ROOT/'outputs/vla_data/manifest.json').read_text(encoding='utf8'))['prompts']
    manifest=dict(seed=20261026,images=len(frames),samples=len(tasks),prompts=prompts,action_shape=[32,6],state_shape=[9],paired_nav_examples=len(pairs),recorded_pose_sources=metadata['sources'],optical=rendered['provenance'],scope='One fixed room, appearance adaptation. Ground-truth poses are used to render synthetic training images and make teacher labels only.',limit='Teacher uses the existing short-horizon velocity-loop approximation; actual flight success requires separate closed-loop checks.',teacher_only_fields=['teacher_qpos','scene targets'],render_recipe='Same Cycles 16-sample scene/camera and JPEG quality 70 as runtime')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
    report=dict(all_tasks_present=bool((np.bincount(arrays['task'],minlength=7)>0).all()),task_counts=np.bincount(arrays['task'],minlength=7).tolist(),sha256=sha(OUT/'audited_samples.npz'),image_manifest_sha256=sha(OUT/'image_checksums.json'),nav_pairs_sha256=sha(OUT/'nav_pairs.npy'),images_hashed=len(hashes),kept_samples=len(tasks),paired_examples=len(pairs),teacher_geometry_is_model_input=False)
    (OUT/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','render','finalize']);args=p.parse_args();globals()[args.stage]()
