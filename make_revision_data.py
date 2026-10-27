"""Build paired-color, latency-length supervision from immutable images/logs.

Geometry is teacher/audit data only. The training whitelist remains RGB, text,
own estimated state and action labels. No scene position enters runtime policy.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import numpy as np

SCALE=np.array([.2,.2,.3,.35,1,1],dtype=np.float32)


def quaternion(roll,pitch,yaw):
    cr,sr=math.cos(roll/2),math.sin(roll/2)
    cp,sp=math.cos(pitch/2),math.sin(pitch/2)
    cy,sy=math.cos(yaw/2),math.sin(yaw/2)
    return [cr*cp*cy+sr*sp*sy,sr*cp*cy-cr*sp*sy,cr*sp*cy+sr*cp*sy,cr*cp*sy-sr*sp*cy]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def rotation(q):
    w,x,y,z=np.asarray(q)/np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


def scene_targets(path):
    world=ET.parse(path).getroot().find("worldbody")
    return {c:np.fromstring(world.find(f"body[@name='{c}_person']").get("pos"),sep=" ") for c in ["blue","red"]}


def visible(qpos,target):
    r=rotation(qpos[3:]);delta=target+[0,0,1.03]-(qpos[:3]+r@[.014,0,.025])
    depth=float(delta@r[:,0]);fv=math.tan(math.radians(32));fh=fv*4/3
    return depth>.1 and abs(delta@(-r[:,1]))<.98*fh*depth and abs(delta@r[:,2])<.98*fv*depth


def teacher_chunk(task,qpos,own,targets,steps=32):
    p=qpos[:3].astype(float).copy();r=rotation(qpos[3:]);heading=math.atan2(r[1,0],r[0,0])
    s=own.astype(float).copy();chunk=[]
    for _ in range(steps):
        a=np.zeros(6)
        if task==3:a[5]=float(s[8]>.5)
        elif s[8]<.5:a[4]=float(task in [0,1,2])
        else:
            a[2]=np.clip(.7*(1-s[3]),-.3,.3)
            if task in [0,1] and s[3]>.8:
                delta=targets[["blue","red"][task]][:2]+[-.9,0]-p[:2]
                # Teach a true zero-velocity stop within the original task
                # tolerance, rather than noisy micromotion around an exact point.
                if np.linalg.norm(delta)>.25:
                    c,ss=math.cos(heading),math.sin(heading)
                    a[:2]=np.array([[c,ss],[-ss,c]])@(.7*delta)
                    norm=np.linalg.norm(a[:2])
                    if norm>.2:a[:2]*=.2/norm
            if task in [4,5] and s[3]>.8:
                error=(math.pi/2 if task==4 else -math.pi/2)-s[6]
                a[3]=0 if abs(error)<.12 else np.clip(.8*error,-.35,.35)
        chunk.append(a/SCALE)
        if s[8]>.5 and task!=3:
            # The external velocity loop requests acceleration v_desired-v.
            # Use its one-second time constant for short-horizon labels.
            s[:2]+=.1*(a[:2]-s[:2])
            c,ss=math.cos(heading),math.sin(heading)
            p[:2]+=.1*(np.array([[c,-ss],[ss,c]])@s[:2])
            p[2]+=.1*a[2];s[3]=p[2]
            s[6]+=.1*a[3];s[7]=a[3];heading-=.1*a[3]
    return np.asarray(chunk,dtype=np.float32)


def build(root,output):
    output.mkdir(parents=True,exist_ok=False);(output/"images").mkdir();(output/"scenes").mkdir()
    original=root/"outputs/vla_data";audit=json.loads((original/"audit.json").read_text())
    prompts=json.loads((original/"manifest.json").read_text(encoding="utf-8"))["prompts"]
    assert sha(original/"audited_samples.npz")==audit["sha256"]
    with np.load(original/"samples.npz") as f:data={k:f[k] for k in f.files}
    first={}
    for i,image in enumerate(data["image"]):first.setdefault(int(image),i)
    scenes={};frames=[];origins=[]
    for scene in range(64):
        path=original/"scenes"/f"{scene:03d}.xml";scenes[scene]=scene_targets(path)
        shutil.copy2(path,output/"scenes"/path.name)
    for image,i in sorted(first.items()):
        s=data["state"][i].copy();pos=data["teacher_position"][i]
        qpos=np.array([*pos,*quaternion(s[4],-s[5],-s[6])],dtype=float)
        # Instruction-relative yaw is distinct from physical camera heading.
        s[6]=0
        frames.append((original/"images"/f"{image:05d}.jpg",image//64,qpos,s,0.))
    for record_name in ["final_policy_evidence","inference_revision_01"]:
        record=root/"outputs/ardupilot"/record_name
        if not (record/"result.json").is_file():raise ValueError("All source flights must be terminal before data collection")
        scene_id=len(scenes);scenes[scene_id]=scene_targets(record/"rescue_scene.xml")
        shutil.copy2(record/"rescue_scene.xml",output/"scenes"/f"{scene_id:03d}.xml")
        manifest=json.loads((record/"verification_manifest.json").read_text())
        for profile in manifest["profiles"]:
            case=record/profile;rows=[json.loads(line) for line in (case/"trace.jsonl").read_text().splitlines()]
            times=np.array([row["t"] for row in rows]);events=json.loads((case/"vla_link_events.json").read_text())
            origins.append(dict(record=record_name,profile=profile,trace_sha256=sha(case/"trace.jsonl"),events_sha256=sha(case/"vla_link_events.json")))
            for event in events:
                if event.get("event")!="inference" or not event.get("image_file"):continue
                file=case/"observations"/event["image_file"]
                if sha(file)!=event["image_sha256"]:raise ValueError("Rollout input JPEG changed")
                capture=event["sim_time_capture"];index=max(0,int(np.searchsorted(times,capture,side="right")-1))
                qpos=np.array(rows[index]["truth"][19:26],dtype=float)
                frames.append((file,scene_id,qpos,np.asarray(event["estimated_state"],dtype=np.float32),capture-times[index]))
    rng=np.random.default_rng(20261024);images=[];tasks=[];states=[];labels=[];poses=[];scene_ids=[];pairs=[];hashes={};offsets=[]
    def add(image,scene,qpos,s,task):
        index=len(tasks);images.append(image);tasks.append(task);states.append(s.copy())
        labels.append(teacher_chunk(task,qpos,s,scenes[scene]));poses.append(qpos);scene_ids.append(scene)
        return index
    for image,(file,scene,qpos,s,offset) in enumerate(frames):
        target=output/"images"/f"{image:05d}.jpg";shutil.copy2(file,target);hashes[target.name]=sha(target);offsets.append(float(offset))
        nav=[]
        for task,color in enumerate(["blue","red"]):
            allowed=s[3]<=.8 or visible(qpos,scenes[scene][color])
            nav.append(add(image,scene,qpos,s,task) if allowed else None)
        if all(i is not None for i in nav) and s[3]>.8:pairs.append(nav)
        for task in range(2,7):
            own=s.copy()
            if task in [4,5] and s[3]>.8:
                sign=1 if task==4 else -1
                own[6]=sign*rng.uniform(-.2,math.pi/2+.25);own[7]=rng.uniform(-.35,.35)
            add(image,scene,qpos,own,task)
            if task in [4,5] and s[3]>.8:
                own=s.copy();own[6]=(math.pi/2 if task==4 else -math.pi/2)+rng.uniform(-.12,.12);own[7]=rng.uniform(-.08,.08)
                add(image,scene,qpos,own,task)
        if image%1000==0:print(json.dumps(dict(images=image,samples=len(tasks))),flush=True)
    arrays=dict(image=np.asarray(images,dtype=np.int32),task=np.asarray(tasks,dtype=np.int16),state=np.asarray(states,dtype=np.float32),
                action=np.asarray(labels,dtype=np.float32),teacher_qpos=np.asarray(poses,dtype=np.float32),teacher_scene=np.asarray(scene_ids,dtype=np.int16))
    if not all(np.isfinite(arrays[k]).all() for k in ["state","action","teacher_qpos"]):raise ValueError("Nonfinite labels")
    if arrays["action"].shape[1:]!=(32,6) or np.abs(arrays["action"]).max()>1.0001:raise ValueError("Action contract violation")
    for a,b in pairs:
        if arrays["task"][a]!=0 or arrays["task"][b]!=1 or arrays["image"][a]!=arrays["image"][b] or not np.array_equal(arrays["state"][a],arrays["state"][b]):raise ValueError("Invalid paired-color supervision")
    np.savez_compressed(output/"audited_samples.npz",**arrays)
    np.save(output/"nav_pairs.npy",np.asarray(pairs,dtype=np.int32))
    (output/"image_checksums.json").write_text(json.dumps(hashes,separators=(",",":")),encoding="utf-8")
    manifest=dict(seed=20261024,images=len(frames),samples=len(tasks),prompts=prompts,action_shape=[32,6],state_shape=[9],
                  paired_nav_examples=len(pairs),recorded_flight_sources=origins,
                  maximum_capture_to_teacher_pose_offset_s=max(offsets),original_audited_data_sha256=audit["sha256"],
                  teacher_only_fields=["teacher_qpos","teacher_scene","scene targets"],
                  changes=["Geometrically visible paired-color instructions for identical image/state", "Navigation relative yaw separated from absolute camera heading", "32-step horizon covers the existing 2.5 s stale limit", "Stop labels use existing goal/rotation tolerances", "Recorded camera/own-state observations augment sampled views"],
                  limit="Future labels use a short-horizon velocity-loop/kinematic-yaw approximation, not dynamically recorded expert trajectories. Pose for rollout labels is the nearest previous decimated truth row; runtime never receives it.")
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    report=dict(all_tasks_present=bool((np.bincount(arrays["task"],minlength=7)>0).all()),task_counts=np.bincount(arrays["task"],minlength=7).tolist(),
                sha256=sha(output/"audited_samples.npz"),image_manifest_sha256=sha(output/"image_checksums.json"),nav_pairs_sha256=sha(output/"nav_pairs.npy"),
                images_hashed=len(hashes),kept_samples=len(tasks),paired_examples=len(pairs),teacher_geometry_is_model_input=False,
                visibility="Geometry checked for every airborne navigation label using the actual camera quaternion, independent of instruction-relative yaw.")
    (output/"audit.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path)
    args=parser.parse_args();root=Path(__file__).parent
    build(root,args.output or root/"outputs/vla_data_revision_02")
