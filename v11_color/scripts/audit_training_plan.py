import sys,json,hashlib
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent;sys.path.insert(0,str(P))
from make_revision_data import visible
plan=json.loads((W/'protocol/plan.json').read_text(encoding='utf-8'));frames=json.loads((W/'protocol/training_frames.json').read_text())
separation=[]
for split in ['development_layouts','heldout_layouts']:
    for layout in plan[split]:
        p=np.array(layout['positions'])[:,:2]
        ordered=[np.linalg.norm(p-np.array(t['positions'])[:,:2]) for t in plan['train_layouts']]
        unordered=[min(np.linalg.norm(p-np.array(t['positions'])[:,:2]),np.linalg.norm(p-np.array(t['positions'])[::-1,:2])) for t in plan['train_layouts']]
        assert min(ordered)>.22 and min(unordered)>1e-6
        separation.append(dict(split=split,layout=layout['name'],minimum_joint_distance_m=float(min(ordered)),minimum_unordered_joint_distance_m=float(min(unordered)),interpretation='Euclidean distance in four-dimensional joint x/y positions; not distance to an individual person'))
both=one=none=ground=0;near=0
for f in frames:
    pos=np.asarray(plan['train_layouts'][f['layout']]['positions']);q=np.asarray(f['qpos']);state=f['state']
    if state[3]<=.8:ground+=1;continue
    vv=[visible(q,p) for p in pos];count=sum(vv)
    if count==2:both+=1
    elif count==1:one+=1
    else:none+=1
    for i,v in enumerate(vv):
        if v and np.linalg.norm(pos[i,:2]+[-.9,0]-q[:2])<=.25:near+=1
for i in range(0,len(frames),2):
    a,b=frames[i:i+2];assert a['qpos']==b['qpos'] and a['state']==b['state'] and a['blue_actor']!=b['blue_actor']
report=dict(separation=separation,training_image_counts=dict(both_centroids_in_fov=both,one_centroid_in_fov=one,no_centroid_in_fov=none,low_or_ground=ground),near_goal_visible_navigation_examples=near,identical_pose_state_shirt_pairs=len(frames)//2,geometry_used_for_teacher_only=True,plan_sha256=hashlib.sha256((W/'protocol/plan.json').read_bytes()).hexdigest(),scope='Held-out exact configurations within the same room and spatial range; not extrapolation to arbitrary layouts')
(W/'protocol/data_split_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
