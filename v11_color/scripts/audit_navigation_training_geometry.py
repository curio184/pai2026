"""Read-only audit of existing training geometry, never evaluation inputs."""
import datetime, hashlib, json, math, sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]; P=W.parent; sys.path.insert(0,str(P))
from make_revision_data import rotation, scene_targets, SCALE

def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    source=W/'data/dataset12_en'
    plan=read(W/'protocol/plan.json')
    first=read(W/'protocol/training_frames.json')
    retained=read(P/'outputs/vla_data_realism_precision_02/poses.json')['frames']
    extra=read(W/'protocol/train05_training_frames.json')
    poses=first+retained+extra
    targets=[]
    for group in [first]:
        for f in group:
            pos=np.asarray(plan['train_layouts'][f['layout']]['positions'])
            targets.append(dict(blue=pos[f['blue_actor']],red=pos[1-f['blue_actor']]))
    targets.extend([scene_targets(W/'scenes/primitive_regression/physics/rescue_scene.xml')]*len(retained))
    for f in extra:
        pos=np.asarray(plan['train_layouts'][f['layout']]['positions'])
        targets.append(dict(blue=pos[f['blue_actor']],red=pos[1-f['blue_actor']]))
    sources=read(source/'image_sources.json'); assert len(sources)==len(poses)==len(targets)==8408
    with np.load(source/'audited_samples.npz') as d:
        images=d['image']; tasks=d['task']; states=d['state']; actions=d['action']
    nav=(tasks<2)&(states[:,8]>.5)&(states[:,3]>.8)
    pairs=sorted(set(zip(images[nav].tolist(),tasks[nav].tolist())))
    bearings=[]
    for i,t in pairs:
        q=np.asarray(poses[i]['qpos']); r=rotation(q[3:]); heading=math.atan2(r[1,0],r[0,0])
        delta=targets[i][['blue','red'][t]][:2]-q[:2]
        angle=math.atan2(delta[1],delta[0])-heading
        bearings.append(math.degrees(math.atan2(math.sin(angle),math.cos(angle))))
    b=np.asarray(bearings)
    result=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope='Existing training metadata only; no policy inference, no optimization, no evaluation inputs.',
        source_audit_sha256=sha(source/'audit.json'), unique_navigation_image_instruction_pairs=len(pairs),
        navigation_examples=int(nav.sum()),
        existing_navigation_yaw_nonzero_values=int(np.count_nonzero(actions[nav,:,3])),
        absolute_bearing_degrees_percentiles=dict(zip(['0','25','50','75','90','95','100'],np.percentile(np.abs(b),[0,25,50,75,90,95,100]).tolist())),
        pairs_over_25_degrees=int((np.abs(b)>25).sum()), pairs_over_35_degrees=int((np.abs(b)>35).sum()),
        caveat='Geometric horizontal bearing is not a detector visibility or success metric. Geometry remains teacher-side only.')
    out=W/'reports/navigation_training_geometry_audit.json'; assert not out.exists()
    out.write_text(json.dumps(result,indent=2),encoding='utf8'); print(json.dumps(result))

if __name__=='__main__': main()
