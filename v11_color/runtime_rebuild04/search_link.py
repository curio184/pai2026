"""Loopback image/action link between Linux physics and the Windows VLA.

Camera rendering and inference run in a background exchange, never in the
physics step. Only JPEG, instruction and estimated state cross into the policy.
"""
import base64
from collections import deque
import io
import json
import math
import socket
import struct
import threading
import time
import hashlib
from pathlib import Path

import numpy as np
from PIL import Image

MAX_PACKET=2*1024*1024


def receive_exact(sock,size):
    result=bytearray()
    while len(result)<size:
        block=sock.recv(size-len(result))
        if not block:raise ConnectionError("VLA peer disconnected")
        result.extend(block)
    return bytes(result)


def receive(sock):
    size=struct.unpack("<I",receive_exact(sock,4))[0]
    if size>MAX_PACKET:raise ValueError("VLA packet too large")
    return json.loads(receive_exact(sock,size))


def send(sock,value):
    payload=json.dumps(value,separators=(",",":"),allow_nan=False).encode()
    if len(payload)>MAX_PACKET:raise ValueError("VLA packet too large")
    sock.sendall(struct.pack("<I",len(payload))+payload)


class CameraLink:
    def __init__(self,scene,port=17866,recording_directory=None):
        self.scene=scene;self.port=port;self.latest=None;self.result=None
        self.lock=threading.Lock();self.stop=threading.Event()
        self.events=deque(maxlen=10000)
        self.recording_directory=Path(recording_directory) if recording_directory else None
        if self.recording_directory:self.recording_directory.mkdir(parents=True,exist_ok=True)
        self.thread=threading.Thread(target=self._run,daemon=True)
        self.thread.start()

    def submit(self,sim_time,qpos,qvel,estimated_state,instruction):
        if len(estimated_state)!=9:raise ValueError("Expected nine estimated features")
        with self.lock:
            self.latest=(float(sim_time),np.asarray(qpos).copy(),np.asarray(qvel).copy(),list(estimated_state),instruction)

    def read(self):
        with self.lock:return dict(self.result) if self.result else None

    def _run(self):
        import os
        os.environ.setdefault("MUJOCO_GL","egl")
        from rescue_scene import Camera
        camera=None
        try:
            camera=Camera(self.scene)
            if hasattr(camera,'provenance'):
                self.events.append(dict(event='camera_provenance',**camera.provenance))
            with socket.socket() as listener:
                listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                listener.bind(("127.0.0.1",self.port));listener.listen(1);listener.settimeout(.5)
                self.events.append(dict(event="listening",port=self.port))
                while not self.stop.is_set():
                    try:connection,address=listener.accept()
                    except socket.timeout:continue
                    self.events.append(dict(event="worker_connected"))
                    with connection:
                        connection.settimeout(20)
                        sequence=0;previous_time=-1
                        while not self.stop.is_set():
                            with self.lock:observation=self.latest
                            if observation is None or observation[0]==previous_time:
                                self.stop.wait(.02);continue
                            sim_time,qpos,qvel,state,instruction=observation
                            previous_time=sim_time
                            start=time.monotonic()
                            rgb=camera.render(qpos,qvel)
                            stream=io.BytesIO();Image.fromarray(rgb).save(stream,format="JPEG",quality=70)
                            jpeg=stream.getvalue();image_file=None
                            if self.recording_directory:
                                image_file=f"{sequence:05d}.jpg"
                                with (self.recording_directory/image_file).open("xb") as handle:handle.write(jpeg)
                            request=dict(version=1,id=sequence,sim_time_capture=sim_time,
                                         rgb_jpeg_base64=base64.b64encode(jpeg).decode(),
                                         state=state,instruction=instruction)
                            send(connection,request)
                            response=receive(connection)
                            action=np.asarray(response.get("action"),dtype=float)
                            if response.get("id")!=sequence or action.shape!=(6,) or not np.isfinite(action).all():
                                raise ValueError("Invalid VLA response")
                            result=dict(id=sequence,sim_time_capture=sim_time,instruction=instruction,
                                        action=action.tolist(),wall_exchange_s=time.monotonic()-start,
                                        inference_s=response.get("inference_s"),policy_kind=response.get("policy_kind","unknown"),
                                        checkpoint_sha256=response.get("checkpoint_sha256"),
                                        action_chunk=response.get("action_chunk"),action_dt_s=response.get("action_dt_s"),
                                        perception=response.get('perception',{}),image_file=image_file,image_sha256=hashlib.sha256(jpeg).hexdigest(),estimated_state=state)
                            with self.lock:self.result=result
                            self.events.append(dict(event="inference",**result));sequence+=1
        except BaseException as error:
            self.events.append(dict(event="link_error",error=repr(error)))
        finally:
            if camera is not None:camera.close()

    def close(self):
        self.stop.set();self.thread.join(timeout=1)


class ActionGate:
    """Bounds, request debounce and stale-output handling, independent of semantics."""
    def __init__(self,chunk_origin="capture"):
        if chunk_origin not in ("capture","receipt","split"):raise ValueError("Unknown chunk execution origin")
        self.chunk_origin=chunk_origin;self.chunk_received_at=None
        self.last_id=None;self.takeoff_count=0;self.land_count=0;self.instruction=None;self.armed_since=None
        self.takeoff_fired=False;self.land_fired=False
        self.selected_chunk_index=None;self.selected_yaw_chunk_index=None;self.horizon_exceeded=False

    def apply(self,packet,sim_time,instruction,armed):
        zero=np.zeros(6,dtype=float)
        self.selected_chunk_index=None;self.selected_yaw_chunk_index=None;self.horizon_exceeded=False
        if armed and self.armed_since is None:self.armed_since=sim_time
        if not armed:self.armed_since=None
        if instruction!=self.instruction:
            self.instruction=instruction;self.takeoff_count=0;self.land_count=0;self.last_id=None
            self.takeoff_fired=False;self.land_fired=False
            self.chunk_received_at=None
        if packet is None:
            if armed and sim_time-self.armed_since>8:
                zero[5]=1;return zero,"watchdog_land"
            return zero,"awaiting_policy"
        age=sim_time-packet["sim_time_capture"]
        if age>8 and armed:
            zero[5]=1;return zero,"watchdog_land"
        if age>2.5:
            self.takeoff_count=0;self.land_count=0
            return zero,"stale_hover"
        if packet["instruction"]!=instruction:return zero,"old_instruction"
        if packet["id"]!=self.last_id:self.chunk_received_at=sim_time
        if packet.get("action_chunk") is not None:
            chunk=np.asarray(packet["action_chunk"],dtype=float)
            dt=float(packet.get("action_dt_s") or 0)
            if chunk.ndim!=2 or chunk.shape[1]!=6 or not len(chunk) or not np.isfinite(chunk).all() or dt<=0:
                return zero,"invalid_chunk_hover"
            # Receipt starts a new plan at its unexecuted head. Capture timing
            # remains available for historical reproduction. Observation age
            # independently controls the unchanged stale/watchdog limits above.
            elapsed=sim_time-self.chunk_received_at if self.chunk_origin=="receipt" else age
            raw_index=max(0,int(elapsed/dt))
            self.selected_chunk_index=min(raw_index,len(chunk)-1)
            self.horizon_exceeded=raw_index>=len(chunk)
            action=chunk[self.selected_chunk_index].copy()
            self.selected_yaw_chunk_index=self.selected_chunk_index
            if self.chunk_origin=="split":
                # Linear labels include velocity-loop rollout; retain their
                # capture-time prediction. The direct yaw-rate channel starts
                # its unexecuted sequence at receipt. Both remain VLA outputs.
                yaw_index=max(0,int((sim_time-self.chunk_received_at)/dt))
                self.selected_yaw_chunk_index=min(yaw_index,len(chunk)-1)
                self.horizon_exceeded=self.horizon_exceeded or yaw_index>=len(chunk)
                action[3]=chunk[self.selected_yaw_chunk_index,3]
        else:action=np.asarray(packet["action"],dtype=float).copy()
        if not np.isfinite(action).all():return zero,"invalid_hover"
        action[:2]=np.clip(action[:2],-.2,.2)
        norm=np.linalg.norm(action[:2])
        if norm>.2:action[:2]*=.2/norm
        action[2]=np.clip(action[2],-.3,.3);action[3]=np.clip(action[3],-.35,.35)
        action[4:]=np.clip(action[4:],0,1)
        new=packet["id"]!=self.last_id
        if new:
            self.last_id=packet["id"]
            self.takeoff_count=self.takeoff_count+1 if action[4]>.7 else 0
            self.land_count=self.land_count+1 if action[5]>.7 else 0
        action[4]=float(new and not armed and self.takeoff_count>=3 and not self.takeoff_fired)
        action[5]=float(new and armed and self.land_count>=3 and not self.land_fired)
        self.takeoff_fired=self.takeoff_fired or action[4]>0
        self.land_fired=self.land_fired or action[5]>0
        return action,"policy"
