"""Versioned integration, preserving original validated flight code."""
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT=Path(sys.argv[1])
HERE=Path(__file__).resolve().parent
def edit(source, replacements, dest):
    text=(ROOT/source).read_text(encoding='utf8')
    for old,new in replacements:
        if text.count(old)!=1: raise ValueError((source,old[:90],text.count(old)))
        text=text.replace(old,new)
    (HERE/dest).write_text(text,encoding='utf8')

edit('vla_link.py',[("image_file=image_file,image_sha256=", "perception=response.get('perception',{}),image_file=image_file,image_sha256=")],'search_link.py')
edit('vla_worker.py',[
    ('import argparse','import sys, os\nsys.path.insert(0,os.environ["RESCUE_PROJECT_ROOT"])\nimport argparse'),
    ('from smolvla_policy import DroneVLA','from smolvla_policy import DroneVLA\nfrom perception import PersonPerception'),
    ('policy=DroneVLA(args.checkpoint)','perception=PersonPerception()\n    policy=DroneVLA(args.checkpoint)'),
    ('response=dict(id=request["id"],','response=dict(perception=perception.detect(rgb),id=request["id"],'),
],'search_worker.py')
perception=(HERE/'perception.py').read_text(encoding='utf8')
(HERE/'confirmation.py').write_text(perception[perception.index('class VisualConfirmation:'):],encoding='utf8')

edit('ardupilot_bridge/plant_c.cpp',[
    ('#include <exception>','#include <exception>\n#include <cmath>'),
    ('p->setStartHeight(0.033f);','''p->setStartHeight(0.033f);
    // Frozen initial pose, before time integration. Look away from people.
    const double heading = 1.5707963267948966;
    p->data()->qpos[3] = std::cos(heading/2);
    p->data()->qpos[4] = 0;
    p->data()->qpos[5] = 0;
    p->data()->qpos[6] = std::sin(heading/2);
    mj_forward(p->model(), p->data());''')
],'plant_search.cpp')

edit('ardupilot_bridge/rescue_mission.py',[
    ('sys.path.insert(0,str(Path(__file__).resolve().parents[1]))','sys.path.insert(0,os.environ["RESCUE_PROJECT_ROOT"])'),
    ('from vla_link import CameraLink,ActionGate','from search_link import CameraLink,ActionGate\nfrom confirmation import VisualConfirmation\nimport shutil\nimport hashlib'),
    ('sequence=["takeoff","hover",args.profile,"land"] if args.profile in ("blue","red","left") else ["takeoff","hover","right","left","land"]',
     '''sequence=["takeoff","hover","right","confirm",args.profile,"report","land"]
    instructions["confirm"]=instructions["hover"]
    instructions["report"]=instructions["hover"]
    visual=VisualConfirmation(args.profile)
    scan_count=1
    discovery=None
    notification=None
    first_observation=None
    mission_failure=None
    upper_instruction="青い服の人を探して" if args.profile=="blue" else "赤い服の人を探して"'''),
    ('while time.monotonic()-start_wall < 180:', 'while time.monotonic()-start_wall < 300:'),
    ('model_packet=link.read()','''model_packet=link.read()
                confirmed=visual.update(model_packet,t)
                if first_observation is None and model_packet:
                    first_observation=dict(id=model_packet['id'],t=model_packet['sim_time_capture'],
                        image_file=model_packet['image_file'],image_sha256=model_packet['image_sha256'],
                        perception=model_packet.get('perception',{}))
                    events.append(dict(t=t,event='initial_camera_observation',**first_observation))'''.replace("dict(t=t,event='initial_camera_observation',**first_observation)","dict(event='initial_camera_observation',**first_observation)")),
    ('elif phase=="hover":','elif phase in ("hover","confirm","report"):'),
    ('navigation_complete=stop_window.update(t,model_action[:2],valid)', 'navigation_complete=stop_window.update(t,model_action[:2],valid) and confirmed'),
    ('if stable:\n                    if settled_since is None:settled_since=t', '''if phase=="confirm":
                    stable=stable and confirmed
                    if not confirmed and t-stage_start>8:
                        if scan_count<4:
                            scan_count+=1
                            sequence[stage_index:stage_index+1]=["right","confirm"]
                            phase="right";stage_start=t;yaw_reference=att.yaw;settled_since=None
                            visual.hits=[]
                            events.append(dict(t=t,event="continue_search",scan_count=scan_count))
                        else:
                            mission_failure="target_not_found"
                            sequence[stage_index+1:]=["land"]
                            navigation_complete=True
                if phase=="report":
                    stable=stable and confirmed
                if phase in (args.profile,"report") and t-stage_start>55:
                    mission_failure="approach_or_report_timeout"
                    sequence[stage_index+1:]=["land"]
                    navigation_complete=True
                if stable:
                    if settled_since is None:settled_since=t'''),
    ('stage_history.append(dict(phase=phase,start=stage_start,end=t))', '''if phase=="confirm" and not mission_failure:
                        discovery=dict(t=t,upper_instruction=upper_instruction,evidence=visual.hits[-3:],scan_count=scan_count)
                        events.append(dict(event="target_discovered",**discovery))
                        (out/"discovery.json").write_text(json.dumps(discovery,indent=2),encoding="utf8")
                    if phase=="report" and not mission_failure:
                        evidence=visual.hits[-1]
                        source=out/"observations"/evidence['image_file']
                        shutil.copy2(source,out/"notification.jpg")
                        if hashlib.sha256((out/"notification.jpg").read_bytes()).hexdigest()!=evidence['image_sha256']:
                            raise RuntimeError("Notification image mismatch")
                        notification=dict(t=t,message="指定した服の色の人物を確認しました",target_color=args.profile,
                            upper_instruction=upper_instruction,image="notification.jpg",evidence=evidence,
                            estimated_state=own_state,transport="local ground-station record; no external message",
                            person_identity_or_medical_state_inferred=False)
                        (out/"notification.json").write_text(json.dumps(notification,indent=2),encoding="utf8")
                        events.append(dict(event="ground_notification",**notification))
                    stage_history.append(dict(phase=phase,start=stage_start,end=t))'''),
    ('if t>110:', 'if t>180:'),
    ('result = dict(ardupilot_commit=AP_PIN,','result = dict(upper_instruction=upper_instruction,discovery=discovery,notification=notification,mission_failure=mission_failure,first_observation=first_observation,initial_heading_degrees=90,ardupilot_commit=AP_PIN,'),
    ('choices=["blue","red","turns","left"]','choices=["blue","red"]'),
],'search_mission.py')

conditions=json.loads((HERE/'scene_conditions.json').read_text())
# Keep exact source geometry and relative STL files; only render sidecars differ.
physics=ROOT/'assets/civic_realism/physics03'
for name in ['clear','fog_light','fog_dense','dust']:
    target=HERE/'scenes'/name/'physics'
    target.mkdir(exist_ok=True)
    for src in physics.iterdir():
        if src.suffix.lower() in ('.stl','.xml'): shutil.copy2(src,target/src.name)
    optical=json.loads((physics/'rescue_scene.render.json').read_text())
    import hashlib
    optical['blend_sha256']=hashlib.sha256((target.parent/'scene.blend').read_bytes()).hexdigest()
    optical['blend_relative']=str(target.parent/'scene.blend')
    (target/'rescue_scene.render.json').write_text(json.dumps(optical,indent=2),encoding='utf8')
print('SEARCH_RUNTIME_PREPARED')
