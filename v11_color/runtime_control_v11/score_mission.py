"""Independent physical-state scoring, run only after the flight process exits.

Person positions are read here for scoring; neither this module nor the scene
targets are imported into the policy worker or flight controller.
"""
import argparse
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np


def longest_hold(times,mask):
    start=None;longest=0.;end=None
    for t,valid in zip(times,mask):
        if valid:
            if start is None:start=float(t)
            if float(t)-start>longest:longest=float(t)-start;end=float(t)
        else:start=None
    return dict(duration_s=longest,end_s=end)


def heading(row):
    w,x,y,z=row[7:11]
    return math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))


def score(record,scene):
    rows=[json.loads(line) for line in (record/"trace.jsonl").read_text().splitlines()]
    if not rows:raise ValueError("No physical flight trace")
    result=json.loads((record/"result.json").read_text())
    events=json.loads((record/"events.json").read_text())
    link=json.loads((record/"vla_link_events.json").read_text())
    last=json.loads((record/"last_messages.json").read_text())
    times=np.array([r["t"] for r in rows]);truth=np.array([r["truth"] for r in rows])
    xy=truth[:,[2,1]]  # physical NED -> scene ENU
    height=-truth[:,3];speed=np.linalg.norm(truth[:,4:6],axis=1)
    phases=np.array([r["phase"] for r in rows])
    world=ET.parse(scene).getroot().find("worldbody")
    persons={color:np.fromstring(world.find(f"body[@name='{color}_person']").get("pos"),sep=" ")[:2] for color in ["blue","red"]}
    goals={color:position+[-.9,0] for color,position in persons.items()}
    holds={}
    for color,goal in goals.items():
        distance=np.linalg.norm(xy-goal,axis=1)
        mask=(phases==color)&(distance<=.25)&(speed<=.08)&(height>=.8)&(height<=1.25)
        holds[color]=dict(goal_scene_xy_m=goal.tolist(),minimum_goal_distance_m=float(distance.min()),
                          physical_hold=longest_hold(times,mask))
    airborne=height>.1
    hover_mask=(phases=="hover")&(speed<=.08)&(np.abs(truth[:,6])<=.08)&(height>=.8)&(height<=1.25)
    hover=longest_hold(times,hover_mask)
    minimum_clearance=min(float(np.linalg.norm(xy[airborne]-p,axis=1).min()) for p in persons.values()) if airborne.any() else None
    heartbeat=last.get("HEARTBEAT",{})
    grounded=bool(height[-1]<.06 and np.max(np.abs(rows[-1]["motor_duty"]))<1e-5 and not (heartbeat.get("base_mode",128)&128))
    policy_requests=dict(takeoff=any(e.get("event")=="policy_takeoff_request" for e in events),
                         land=any(e.get("event")=="land_request" and e.get("source")=="policy" for e in events))
    policy_evidence=[e for e in link if e.get("event")=="inference" and e.get("policy_kind")=="SmolVLA" and e.get("checkpoint_sha256")]
    rotations={}
    for phase,expected in [("right",90),("left",-90)]:
        idx=np.where(phases==phase)[0]
        if len(idx)<2:rotations[phase]=dict(completed=False);continue
        angles=np.unwrap([heading(truth[i]) for i in idx])
        change=float(np.rad2deg(angles[-1]-angles[0]))
        final=idx[times[idx]>=times[idx[-1]]-2]
        stable=bool(np.max(np.abs(truth[final,31]))<.08 and np.max(speed[final])<.08)
        rotations[phase]=dict(clockwise_rotation_deg=change,expected_deg=expected,
                              stopped=stable,completed=bool(abs(change-expected)<10 and stable))
    takeoff=bool(height[0]<.1 and height.max()>.85 and policy_requests["takeoff"])
    profile=result["profile"]
    task=(holds[profile]["physical_hold"]["duration_s"]>=3 if profile in holds else
          rotations["left"]["completed"] if profile=="left" else
          all(rotations[p]["completed"] for p in ["right","left"]))
    watchdog=any(e.get("event")=="land_request" and e.get("source")=="watchdog_land" for e in events)
    delays=[r["t"]-r["model_capture_time"] for r in rows if r.get("action_source")=="policy" and r.get("model_capture_time") is not None]
    success=bool(policy_evidence and takeoff and hover["duration_s"]>=3 and task and grounded and policy_requests["land"] and not watchdog and minimum_clearance is not None and minimum_clearance>=.45)
    report=dict(success=success,profile=profile,scoring_uses_truth_after_flight=True,
                learned_policy_provenance=bool(policy_evidence),checkpoints=sorted(set(e["checkpoint_sha256"] for e in policy_evidence)),
                takeoff=takeoff,policy_requests=policy_requests,grounded_disarmed_motors_off=grounded,
                goal_holds=holds,rotations=rotations,minimum_person_clearance_m=minimum_clearance,
                explicit_hover_instruction_hold=hover,
                watchdog_landing=watchdog,maximum_height_m=float(height.max()),
                observation_age_s=dict(mean=float(np.mean(delays)),p95=float(np.percentile(delays,95)),max=float(np.max(delays))) if delays else None,
                limits=dict(goal_tolerance_m=.25,horizontal_speed_m_s=.08,hold_s=3,altitude_m=[.8,1.25],minimum_person_clearance_m=.45,rotation_tolerance_deg=10),
                note="Simulator task evidence only; real hardware feasibility is a separate required gate.")
    output=record/"physical_score.json"
    if output.exists():raise FileExistsError("Scoring evidence already exists")
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("record",type=Path);p.add_argument("--scene",type=Path,required=True)
    a=p.parse_args();score(a.record,a.scene)
