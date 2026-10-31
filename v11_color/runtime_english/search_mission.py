"""One recorded ArduPilot + StampFly physics integration check; no policy training.

Only localhost transports. Ground truth is used for sensor synthesis and scoring,
never injected as navigation pose/velocity. No force-arm, teleport or motor priming.
"""
import os
os.environ["MAVLINK20"] = "1"
import argparse
import ctypes
import json
import math
from pathlib import Path
import socket
import struct
import subprocess
import time
import sys
sys.path.insert(0,os.environ["RESCUE_PROJECT_ROOT"])
from search_link import CameraLink,ActionGate
from confirmation import VisualConfirmation
import shutil
import hashlib
from flight_progress import StopCommandWindow

import numpy as np
from pymavlink import mavutil

AP_PIN = "38687117133582049734ebd39f8a7af6f487716a"


def run(args):
    commands={"青い服の人を探して":"blue", "赤い服の人を探して":"red"}
    if args.instruction is not None:
        if args.instruction not in commands: raise ValueError("Supported commands: "+str(list(commands)))
        args.profile=commands[args.instruction]
    out = args.output
    out.mkdir(parents=True, exist_ok=False)  # Each record is immutable.
    lib = ctypes.CDLL(str(args.build/"libstampfly_plant.so"))
    lib.sf_create.argtypes = [ctypes.c_char_p, ctypes.c_float]; lib.sf_create.restype = ctypes.c_void_p
    lib.sf_step.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double), ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
    lib.sf_destroy.argtypes = [ctypes.c_void_p]
    build_meta=json.loads((args.build/"build_result.json").read_text())
    assembly_mass=float(build_meta["mass_kg"])
    ptr = lib.sf_create(str(args.scene).encode(), assembly_mass)
    if not ptr:
        raise RuntimeError("Plant init failed")
    state = np.zeros(32, dtype=np.float64)
    duty = np.zeros(4, dtype=np.float64)
    native_ptr = lambda a: a.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    lib.sf_step(ptr, native_ptr(duty), 0, native_ptr(state))
    # Published hardware defaults, with explicit simulation and navigation setup.
    defaults = (args.ardupilot/"libraries/AP_HAL_ESP32/hwdef/esp32s3m5stampfly/defaults.parm").read_text()
    defaults += """
# Simulation transport/model only; no blanket arming-check bypass.
FRAME_TYPE 1
SIM_RATE_HZ 600
SIM_GPS1_ENABLE 0
SIM_GPS2_ENABLE 0
GPS1_TYPE 0
GPS2_TYPE 0
COMPASS_ENABLE 0
COMPASS_USE 0
EK3_SRC1_YAW 0
EK3_SRC1_POSXY 0
EK3_SRC1_VELXY 5
EK3_SRC1_POSZ 1
EK3_SRC1_VELZ 0
FLOW_TYPE 5
FLOW_POS_Z 0.020
RNGFND1_TYPE 10
RNGFND1_MIN 0.02
RNGFND1_MAX 6
RNGFND1_ORIENT 25
RNGFND1_POS_Z 0.020
BATT_MONITOR 4
BATT_VOLT_PIN 13
BATT_CURR_PIN 12
# SITL_State_Common::set_voltage_current_pins uses the 3DR divider.
BATT_VOLT_MULT 10.1
BATT_AMP_PERVLT 17
BRD_SAFETY_DEFLT 0
LOG_BACKEND_TYPE 1
SERIAL0_PROTOCOL 2
WP_SPD_UP 1.0
WP_SPD_DN 0.5
MOT_HOVER_LEARN 0
MOT_BAT_VOLT_MAX 4.2
MOT_BAT_VOLT_MIN 3.4
RC1_MIN 1000
RC1_MAX 2000
RC2_MIN 1000
RC2_MAX 2000
RC3_MIN 1000
RC3_MAX 2000
RC4_MIN 1000
RC4_MAX 2000
"""
    # Approximate initial collective seed from the plant's equal-motor hover
    # equilibrium at its initial battery voltage. This simple expo mapping does
    # not invert AP's spin range/voltage compensation or account for offset CG.
    # It is not a measured hardware hover setting or a fitted controller gain.
    meta = json.loads((args.build/"build_result.json").read_text())
    h = meta["hover_duty_nominal"]
    normalized = (0.55*h + 0.45*h*h)
    defaults += f"\nMOT_THST_HOVER {normalized:.9f}\n"
    parms = out/"defaults.parm"; parms.write_text(defaults)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 9002)); sock.settimeout(0.2)
    command = [str(args.ardupilot/"build/sitl/bin/arducopter"), "--model", "JSON:127.0.0.1", "--speedup", "1", "--defaults", str(parms), "--home", "35.0,139.0,10,0", "--serial0=tcp:5760", "--wipe"]
    log = (out/"ardupilot.log").open("w")
    proc = subprocess.Popen(command, cwd=out, stdout=log, stderr=subprocess.STDOUT)
    link=CameraLink(args.scene,args.port,recording_directory=out/"observations");gate=ActionGate(chunk_origin=args.chunk_origin)
    mav = None
    start_wall = time.monotonic()
    last_frame = None; reply = b""; last_sensor = -1; last_stream = -1; last_control = -1
    events = []; rows = []; messages = {}; actions = set(); rng = np.random.default_rng(20261023)
    armed_at = None; target_alt = 1.0; stopped = "timeout"
    att = None; local = None; origin_z = None
    phase="takeoff";stage_start=0.;settled_since=None;is_armed=False;yaw_reference=0.;yaw_target=0.
    model_action=np.zeros(6);action_source="initializing";own_state=None
    model_packet=None;stage_history=[]
    instructions={
        "takeoff":"Take off and hover at one meter.",
        "blue":"Approach the person wearing blue and stop.",
        "red":"Approach the person wearing red and stop.",
        "right":"Turn clockwise ninety degrees and stop.",
        "left":"Turn counterclockwise ninety degrees and stop.",
        "hover":"Stop and hover here.",
        "land":"Land and stop the motors."}
    sequence=["takeoff","hover","right","confirm",args.profile,"report","land"]
    instructions["confirm"]=instructions["hover"]
    instructions["report"]=instructions["hover"]
    instructions["reacquire"]=instructions["hover"]
    visual=VisualConfirmation(args.profile)
    scan_count=1
    discovery=None
    notification=None
    first_observation=None
    mission_failure=None
    search_start_observation=None
    resume_phase=None
    upper_instruction="青い服の人を探して" if args.profile=="blue" else "赤い服の人を探して"
    stage_index=0
    stop_window=StopCommandWindow()
    try:
        while time.monotonic()-start_wall < 300:
            if proc.poll() is not None:
                stopped = f"ArduPilot exited {proc.returncode}"; break
            try:
                packet, remote = sock.recvfrom(256)
            except socket.timeout:
                continue
            if len(packet) != 40:
                raise RuntimeError(f"Unexpected servo packet size {len(packet)}")
            magic, rate, frame, *pwm = struct.unpack("<HHI16H", packet)
            if magic != 18458 or rate == 0:
                raise RuntimeError("Invalid servo packet")
            if frame == last_frame:
                sock.sendto(reply, remote); continue
            last_frame = frame
            # AP channels FR,RL,FL,RR -> plant FR,RR,RL,FL.
            duty[:] = np.clip((np.array([pwm[0], pwm[3], pwm[1], pwm[2]])-1000)/1000, 0, 1)
            lib.sf_step(ptr, native_ptr(duty), 1.0/rate, native_ptr(state))
            t = float(state[0])
            if not np.isfinite(state).all():
                raise RuntimeError("Nonfinite physics")
            payload = dict(timestamp=t, imu=dict(gyro=state[11:14].tolist(), accel_body=state[14:17].tolist()),
                           position=state[1:4].tolist(), velocity=state[4:7].tolist(), quaternion=state[7:11].tolist(),
                           battery=dict(voltage=float(state[17]), current=0.0),
                           rc={f"rc_{i}": (1000 if i in (3,5,6,7) else 1500) for i in range(1,9)})
            reply = ("\n"+json.dumps(payload, separators=(",", ":"))+"\n").encode()
            sock.sendto(reply, remote)
            if mav is None:
                try:
                    mav = mavutil.mavlink_connection("tcp:127.0.0.1:5760", source_system=255, autoreconnect=False)
                    events.append(dict(t=t, event="mavlink_connected"))
                except OSError:
                    continue
            while True:
                msg = mav.recv_match(blocking=False)
                if msg is None:
                    break
                kind = msg.get_type(); messages[kind] = msg.to_dict()
                if kind in ("STATUSTEXT", "COMMAND_ACK"):
                    events.append(dict(t=t, event=kind, message=msg.to_dict()))
                if kind == "ATTITUDE": att = msg
                if kind == "LOCAL_POSITION_NED":
                    local = msg
                    if armed_at is None:origin_z=local.z
                if kind == "HEARTBEAT":
                    is_armed=bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                    if is_armed and armed_at is None:
                        armed_at=t;yaw_target=att.yaw if att else 0.
                        events.append(dict(t=t,event="armed"))
            if t-last_stream >= 1:
                last_stream = t
                mav.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
                if "streams" not in actions and t > 3:
                    mav.mav.request_data_stream_send(1, 1, mavutil.mavlink.MAV_DATA_STREAM_ALL, 20, 1)
                    # Local coordinate anchor only; no aircraft/target truth.
                    mav.mav.set_gps_global_origin_send(1, 350000000, 1390000000, 10000)
                    actions.add("streams")
            if t-last_sensor >= 0.02:
                last_sensor = t
                w,x,y,z = state[7:11]
                rot = np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                                [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                                [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
                # Sensor sits 20 mm below the original body origin.
                distance = max(0.001, (-state[3]-0.020*rot[2,2])/max(0.05, rot[2,2]))
                valid = .08 <= distance <= 6 and rot[2,2] > .5
                body_v = rot.T @ state[4:7] + np.cross(state[11:14], [0,0,.020])
                flow_x = -body_v[1]/distance+state[11]+rng.normal(0,.02)
                flow_y = body_v[0]/distance+state[12]+rng.normal(0,.02)
                old_source = mav.mav.srcSystem
                mav.mav.srcSystem = 200
                mav.mav.optical_flow_send(int(t*1e6),0,0,0,0.0,0.0,255 if valid else 0,distance,flow_x,flow_y)
                measured = float(np.clip(distance+rng.normal(0,.01),.02,6))
                mav.mav.distance_sensor_send(int(t*1000),2,600,int(measured*100),0,0,25,1)
                mav.mav.srcSystem = old_source
            if t > 12 and "mode" not in actions:
                mav.mav.set_mode_send(1,mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,20) # GUIDED_NOGPS
                actions.add("mode"); events.append(dict(t=t,event="request_guided_nogps"))
            if t-last_control >= .05 and local is not None and att is not None and origin_z is not None:
                control_dt=.05 if last_control<0 else min(.1,t-last_control)
                last_control=t
                c,s=math.cos(att.yaw),math.sin(att.yaw)
                velocity=np.array([[c,s],[-s,c]])@np.array([local.vx,local.vy])
                alt=origin_z-local.z
                relative_yaw=math.atan2(math.sin(att.yaw-yaw_reference),math.cos(att.yaw-yaw_reference))
                own_state=[float(velocity[0]),float(-velocity[1]),-local.vz,alt,att.roll,att.pitch,relative_yaw,att.yawspeed,float(is_armed)]
                if phase in (args.profile,"report") and visual.last_seen is not None and t-visual.last_seen>3.0:
                    resume_phase=phase
                    sequence[stage_index:stage_index]=["reacquire"]
                    stage_history.append(dict(phase=phase,start=stage_start,end=t,interrupted="visual_target_lost"))
                    phase="reacquire";stage_start=t;settled_since=None;stop_window.reset()
                    events.append(dict(t=t,event="visual_target_lost_hover"))
                prompt=instructions[phase]
                link.submit(t,state[19:26],state[26:32],own_state,prompt)
                model_packet=link.read()
                confirmed=visual.update(model_packet,t)
                if first_observation is None and model_packet:
                    first_observation=dict(id=model_packet['id'],t=model_packet['sim_time_capture'],
                        image_file=model_packet['image_file'],image_sha256=model_packet['image_sha256'],
                        perception=model_packet.get('perception',{}))
                    events.append(dict(event='initial_camera_observation',**first_observation))
                if t>=16:
                    model_action,action_source=gate.apply(model_packet,t,prompt,is_armed)
                else:model_action=np.zeros(6);action_source="autopilot_initializing"
                if model_action[4]>0:
                    mav.mav.command_long_send(1,1,mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,0,1,0,0,0,0,0,0)
                    events.append(dict(t=t,event="policy_takeoff_request"))
                if model_action[5]>0 and "land" not in actions:
                    mav.mav.set_mode_send(1,1,9);actions.add("land")
                    events.append(dict(t=t,event="land_request",source=action_source))
                desired=np.array([model_action[0],-model_action[1]])
                accel = np.clip(desired-velocity,-.8,.8)
                roll = math.atan2(accel[1],9.81)
                pitch = -math.atan2(accel[0],9.81)
                cr,sr = math.cos(roll/2),math.sin(roll/2)
                cp,sp = math.cos(pitch/2),math.sin(pitch/2)
                yaw_target+=float(model_action[3])*control_dt
                cy,sy = math.cos(yaw_target/2),math.sin(yaw_target/2)
                q = [cr*cp*cy+sr*sp*sy,sr*cp*cy-cr*sp*sy,cr*sp*cy+sr*cp*sy,cr*cp*sy-sr*sp*cy]
                # Pinned firmware maps [0,.5] to WP_SPD_DN and [.5,1] to WP_SPD_UP.
                thrust=.5+float(model_action[2])/(2*(1.0 if model_action[2]>=0 else .5))
                if is_armed and "land" not in actions:
                    mav.mav.set_attitude_target_send(int(t*1000),1,1,7,q,0,0,0,thrust)
                stable=False;navigation_complete=False
                if phase=="takeoff":stable=is_armed and alt>.85 and abs(local.vz)<.08
                elif phase in ("hover","confirm","report","reacquire"):
                    stable=is_armed and .85<alt<1.2 and abs(local.vz)<.08 and np.linalg.norm(velocity)<.08 and action_source=="policy"
                elif phase in ("blue","red"):
                    valid=is_armed and t-stage_start>3 and np.linalg.norm(velocity)<.08 and action_source=="policy"
                    navigation_complete=stop_window.update(t,model_action[:2],valid) and confirmed
                elif phase in ("right","left"):
                    target=math.pi/2 if phase=="right" else -math.pi/2
                    # This is a visual search, not the separate 90-degree accuracy task.
                    # A confirmed target + settled, substantial scan ends this view.
                    stable=abs(att.yawspeed)<.08 and abs(relative_yaw)>.65 and confirmed
                    # If no target is seen, finish a coarse quarter turn before the next view.
                    if not confirmed:
                        stable=abs(relative_yaw-target)<.25 and abs(att.yawspeed)<.08
                if phase=="confirm":
                    stable=stable and confirmed
                    # VisualConfirmation already requires three distinct, tracked images.
                    # Waiting another 3.25 s here adds no new acceptance evidence.
                    navigation_complete=stable
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
                if phase in ("report","reacquire"):
                    stable=stable and confirmed
                    # Approach completion already required the stop-command window.
                    navigation_complete=stable
                if phase=="reacquire" and t-stage_start>12:
                    mission_failure="target_lost_after_discovery"
                    sequence[stage_index+1:]=["land"]
                    navigation_complete=True
                if phase in (args.profile,"report") and t-stage_start>55:
                    mission_failure="approach_or_report_timeout"
                    sequence[stage_index+1:]=["land"]
                    navigation_complete=True
                if stable:
                    if settled_since is None:settled_since=t
                else:settled_since=None
                if (navigation_complete or (settled_since is not None and t-settled_since>3.25)) and stage_index<len(sequence)-1:
                    if phase=="hover":
                        search_start_observation=dict(id=model_packet['id'],t=model_packet['sim_time_capture'],
                            image_file=model_packet['image_file'],image_sha256=model_packet['image_sha256'],
                            perception=model_packet.get('perception',{}),estimated_state=own_state)
                        (out/"search_start_observation.json").write_text(json.dumps(search_start_observation,indent=2),encoding="utf8")
                        events.append(dict(event="search_started",**search_start_observation))
                    if phase=="confirm" and not mission_failure:
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
                    stage_history.append(dict(phase=phase,start=stage_start,end=t))
                    stage_index+=1;phase=sequence[stage_index];stage_start=t;settled_since=None;yaw_reference=att.yaw
                    stop_window.reset()
                    events.append(dict(t=t,event="instruction_changed",phase=phase))
                if armed_at is not None and not is_armed and t-armed_at>5 and "land" not in actions:
                    stopped="unexpected_disarm";mission_failure="autopilot_landed_before_mission_completion";break
                if "land" in actions and armed_at is not None and not is_armed:
                    stopped="landed_and_disarmed";break
            if frame % 12 == 0:
                rows.append(dict(t=t, truth=state.tolist(), motor_duty=duty.tolist(), phase=phase,
                                 estimated_alt_m=-local.z if local is not None else None,
                                 estimated_attitude=[att.roll,att.pitch,att.yaw] if att is not None else None,
                                 model_action=model_action.tolist(),action_source=action_source,estimated_state=own_state,
                                 model_capture_time=model_packet["sim_time_capture"] if model_packet else None,
                                 chunk_index=gate.selected_chunk_index,chunk_horizon_exceeded=gate.horizon_exceeded,
                                 yaw_chunk_index=gate.selected_yaw_chunk_index,
                                 chunk_execution_origin=args.chunk_origin))
            if t>120 and phase!="land":
                mission_failure="mission_deadline"
                phase="land";stage_start=t
                sequence=["land"];stage_index=0
                events.append(dict(t=t,event="mission_deadline_normal_land"))
            if t>150:
                stopped="mission_deadline_reached";break
        if armed_at is not None and mav is not None:
            # No hardware transport; stop this simulation through normal land mode.
            mav.mav.set_mode_send(1,1,9)
    finally:
        link.close()
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait()
        log.close(); sock.close(); lib.sf_destroy(ptr)
        if mav is not None: mav.close()
        (out/"trace.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
        (out/"events.json").write_text(json.dumps(events,indent=2)+"\n")
        (out/"last_messages.json").write_text(json.dumps(messages,indent=2,
            default=lambda value: list(value) if isinstance(value, (bytes,bytearray)) else str(value))+"\n")
        (out/"vla_link_events.json").write_text(json.dumps(list(link.events),indent=2)+"\n")
        (out/"stages.json").write_text(json.dumps(stage_history,indent=2)+"\n")
    alts = [-r["truth"][3] for r in rows]
    result = dict(search_start_observation=search_start_observation,upper_instruction=upper_instruction,discovery=discovery,notification=notification,mission_failure=mission_failure,first_observation=first_observation,initial_heading_degrees=90,ardupilot_commit=AP_PIN, controller_source_modified=False, mass_kg=assembly_mass,
                  success_verified=False,profile=args.profile,armed_at_s=armed_at,max_physical_altitude_m=max(alts,default=0),
                  final_physical_altitude_m=alts[-1] if alts else None, stop_reason=stopped,
                  actual_rate_hz=rate if last_frame is not None else None,
                  goal_altitude_m=1.0, hover_scoring_band_m=[.75,1.25],
                  truth_navigation_enabled=False, sensor_model_calibrated=False,
                  gains_searched=False,vla_used=any(e.get("policy_kind")=="SmolVLA" for e in link.events),
                  chunk_execution_origin=args.chunk_origin,
                  note="Requires independent physical-state scoring; reaching a scripted stage is not proof of task success.")
    (out/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ardupilot",type=Path,default=Path.home()/"physical_ai_ardupilot/ardupilot")
    p.add_argument("--build",type=Path,default=Path.home()/"physical_ai_ardupilot/bridge")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--scene",type=Path,required=True)
    p.add_argument("--profile",choices=["blue","red"],default="blue")
    p.add_argument("--instruction",type=str)
    p.add_argument("--port",type=int,default=17866)
    p.add_argument("--chunk-origin",choices=["capture","receipt","split"],default="capture")
    run(p.parse_args())
