"""One recorded ArduPilot + StampFly physics integration check; no policy training.

Only localhost transports. Ground truth is used for sensor synthesis and scoring,
never injected as navigation pose/velocity. No force-arm, teleport or motor priming.
"""
import os
os.environ["MAVLINK20"] = "1"
import argparse
import ctypes
import json
import hashlib
import shutil
import math
from pathlib import Path
import socket
import struct
import subprocess
import time

import numpy as np
from pymavlink import mavutil

AP_PIN = "38687117133582049734ebd39f8a7af6f487716a"


def run(args):
    out = args.output
    sensor_rate=getattr(args,"sensor_rate_hz",100.)
    sensor_range=getattr(args,"sensor_range_m",8.)
    if sensor_rate<=0 or sensor_range<=0:raise ValueError("Sensor rate/range must be positive")
    out.mkdir(parents=True, exist_ok=False)  # Each record is immutable.
    assembly_mass=json.loads((args.build/"build_result.json").read_text())["mass_kg"]
    snapshot=out/"source_snapshot";snapshot.mkdir()
    for file in [Path(__file__),args.build/"build_result.json",args.build/"stampfly_payload.xml"]:
        shutil.copy2(file,snapshot/file.name)
    lib = ctypes.CDLL(str(args.build/"libstampfly_plant.so"))
    lib.sf_create.argtypes = [ctypes.c_char_p, ctypes.c_float]; lib.sf_create.restype = ctypes.c_void_p
    lib.sf_step.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double), ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
    lib.sf_destroy.argtypes = [ctypes.c_void_p]
    ptr = lib.sf_create(str(args.build/"stampfly_payload.xml").encode(), assembly_mass)
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
RNGFND1_MAX 8
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
    defaults += f"\nMOT_THST_HOVER {normalized:.9f}\nRNGFND1_MAX {sensor_range:g}\n"
    parms = out/"defaults.parm"; parms.write_text(defaults)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 9002)); sock.settimeout(0.2)
    command = [str(args.ardupilot/"build/sitl/bin/arducopter"), "--model", "JSON:127.0.0.1", "--speedup", "1", "--defaults", str(parms), "--home", "35.0,139.0,10,0", "--serial0=tcp:5760", "--wipe"]
    log = (out/"ardupilot.log").open("w")
    proc = subprocess.Popen(command, cwd=out, stdout=log, stderr=subprocess.STDOUT)
    mav = None
    start_wall = time.monotonic()
    last_frame = None; reply = b""; last_sensor = -1; last_stream = -1; last_control = -1
    events = []; rows = []; messages = {}; actions = set(); rng = np.random.default_rng(20261023)
    armed_at = None; target_alt = 1.0; stopped = "timeout"
    att = None; local = None; origin_z = None; stop_anchor = None; phase = "initializing"
    try:
        while time.monotonic()-start_wall < 110:
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
                if kind == "LOCAL_POSITION_NED": local = msg
                if kind == "HEARTBEAT" and msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED and armed_at is None:
                    armed_at = t; origin_z = local.z if local else 0.0
                    events.append(dict(t=t, event="armed"))
            if t-last_stream >= 1:
                last_stream = t
                mav.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
                if "streams" not in actions and t > 3:
                    mav.mav.request_data_stream_send(1, 1, mavutil.mavlink.MAV_DATA_STREAM_ALL, 20, 1)
                    # Local coordinate anchor only; no aircraft/target truth.
                    mav.mav.set_gps_global_origin_send(1, 350000000, 1390000000, 10000)
                    actions.add("streams")
            if t-last_sensor >= 1/sensor_rate:
                last_sensor = t
                w,x,y,z = state[7:11]
                rot = np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                                [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                                [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
                # Sensor sits 20 mm below the original body origin.
                distance = max(0.001, (-state[3]-0.020*rot[2,2])/max(0.05, rot[2,2]))
                valid = .08 <= distance <= sensor_range and rot[2,2] > .5
                body_v = rot.T @ state[4:7] + np.cross(state[11:14], [0,0,.020])
                flow_x = -body_v[1]/distance+state[11]+rng.normal(0,.02)
                flow_y = body_v[0]/distance+state[12]+rng.normal(0,.02)
                old_source = mav.mav.srcSystem
                mav.mav.srcSystem = 200
                mav.mav.optical_flow_send(int(t*1e6),0,0,0,0.0,0.0,255 if valid else 0,distance,flow_x,flow_y)
                measured = float(np.clip(distance+rng.normal(0,.01),.02,sensor_range))
                mav.mav.distance_sensor_send(int(t*1000),2,int(sensor_range*100),int(measured*100),0,0,25,1)
                mav.mav.srcSystem = old_source
            if t > 12 and "mode" not in actions:
                mav.mav.set_mode_send(1,mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,20) # GUIDED_NOGPS
                actions.add("mode"); events.append(dict(t=t,event="request_guided_nogps"))
            if t > 16 and "arm" not in actions:
                mav.mav.command_long_send(1,1,mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,0,1,0,0,0,0,0,0)
                actions.add("arm"); events.append(dict(t=t,event="request_arm_normal_checks"))
            if armed_at is not None and t-last_control >= .05 and local is not None and att is not None:
                last_control = t
                elapsed = t-armed_at
                alt = origin_z-local.z
                if args.exercise == "rotation":
                    phase = "takeoff" if elapsed < 15 else "rotate" if elapsed < 21 else "stop" if elapsed < 29 else "land"
                else:
                    phase = "takeoff" if elapsed < 15 else "forward" if elapsed < 18 else "stop" if elapsed < 26 else "land"
                desired = np.array([.2,0.0]) if phase == "forward" else np.zeros(2)
                yaw = att.yaw
                c,s = math.cos(yaw),math.sin(yaw)
                ned_to_body = np.array([[c,s],[-s,c]])
                velocity = ned_to_body @ np.array([local.vx,local.vy])
                if phase == "stop":
                    if stop_anchor is None: stop_anchor = np.array([local.x,local.y])
                    desired = np.clip(ned_to_body @ (stop_anchor-np.array([local.x,local.y]))*.5,-.2,.2)
                # Fixed outer-loop pole 1/s, safely below the 150 Hz attitude loop.
                # Uses estimated velocity only, not physical state or target truth.
                accel = np.clip(desired-velocity,-.8,.8)
                roll = math.atan2(accel[1],9.81)
                pitch = -math.atan2(accel[0],9.81)
                cr,sr = math.cos(roll/2),math.sin(roll/2)
                cp,sp = math.cos(pitch/2),math.sin(pitch/2)
                # Relative heading from the onboard estimator, not simulator truth.
                yaw_target = float(np.clip((elapsed-15)*math.pi/12,0,math.pi/2)) if args.exercise == "rotation" else 0.0
                cy,sy = math.cos(yaw_target/2),math.sin(yaw_target/2)
                q = [cr*cp*cy+sr*sp*sy,sr*cp*cy-cr*sp*sy,cr*sp*cy+sr*cp*sy,cr*cp*sy-sr*sp*cy]
                thrust = .5 if elapsed < 2 else .5+float(np.clip((target_alt-alt)*.15,-.08,.12))
                if phase != "land":
                    mav.mav.set_attitude_target_send(int(t*1000),1,1,7,q,0,0,0,thrust)
                elif "land" not in actions:
                    mav.mav.set_mode_send(1,1,9); actions.add("land")
                    events.append(dict(t=t,event="land_requested"))
            if frame % 12 == 0:
                rows.append(dict(t=t, truth=state.tolist(), motor_duty=duty.tolist(), phase=phase,
                                 estimated_alt_m=-local.z if local is not None else None,
                                 estimated_attitude=[att.roll,att.pitch,att.yaw] if att is not None else None))
            if t >= (armed_at+(41 if args.exercise == "rotation" else 38) if armed_at else 27):
                stopped = "check_duration_reached"; break
        if armed_at is not None and mav is not None:
            # No hardware transport; stop this simulation through normal land mode.
            mav.mav.set_mode_send(1,1,9)
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait()
        log.close(); sock.close(); lib.sf_destroy(ptr)
        if mav is not None: mav.close()
        (out/"trace.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
        (out/"events.json").write_text(json.dumps(events,indent=2)+"\n")
        (out/"last_messages.json").write_text(json.dumps(messages,indent=2,
            default=lambda value: list(value) if isinstance(value, (bytes,bytearray)) else str(value))+"\n")
    alts = [-r["truth"][3] for r in rows]
    stop_end = 29 if args.exercise == "rotation" else 26
    window = [r for r in rows if armed_at is not None and armed_at+stop_end-5 <= r["t"] <= armed_at+stop_end]
    in_band = bool(window) and all(.75 <= -r["truth"][3] <= 1.25 and math.hypot(*r["truth"][4:6]) < .2 for r in window)
    result = dict(ardupilot_commit=AP_PIN, controller_source_modified=False, mass_kg=assembly_mass,
                  sensor_rate_hz=sensor_rate,sensor_range_m=sensor_range,
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  hover_pass=in_band, exercise=args.exercise, armed_at_s=armed_at, max_physical_altitude_m=max(alts,default=0),
                  final_physical_altitude_m=alts[-1] if alts else None, stop_reason=stopped,
                  actual_rate_hz=rate if last_frame is not None else None,
                  goal_altitude_m=1.0, hover_scoring_band_m=[.75,1.25],
                  truth_navigation_enabled=False, sensor_model_calibrated=False,
                  gains_searched=False, vla_used=False, note="Flight integration check only; not a rescue or sim-to-real result.")
    (out/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ardupilot",type=Path,default=Path.home()/"physical_ai_ardupilot/ardupilot")
    p.add_argument("--build",type=Path,default=Path.home()/"physical_ai_ardupilot/bridge")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--exercise",choices=["translation","rotation"],default="translation")
    p.add_argument("--sensor-rate-hz",type=float,default=100.)
    p.add_argument("--sensor-range-m",type=float,default=8.)
    run(p.parse_args())
