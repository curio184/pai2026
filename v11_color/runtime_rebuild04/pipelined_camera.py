"""Latest-frame camera/VLA pipeline, without changing optics or model settings.

Rendering and policy exchange have separate threads. The bounded single-frame
buffer overwrites obsolete frames; there is never a queue of pending images.
Only images actually sent to the model are saved as model-input observations.
"""
import base64,hashlib,io,socket,threading,time
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image
from vla_link import receive,send

class CameraLink:
    def __init__(self,scene,port=17866,recording_directory=None):
        self.scene=scene;self.port=port;self.latest=None;self.result=None;self.frame=None
        self.lock=threading.Lock();self.stop=threading.Event();self.events=deque(maxlen=10000)
        self.recording_directory=Path(recording_directory) if recording_directory else None
        if self.recording_directory:self.recording_directory.mkdir(parents=True,exist_ok=True)
        self.render_thread=threading.Thread(target=self._render,daemon=True)
        self.thread=threading.Thread(target=self._run,daemon=True)
        self.render_thread.start();self.thread.start()

    def submit(self,sim_time,qpos,qvel,estimated_state,instruction):
        if len(estimated_state)!=9:raise ValueError('Expected nine estimated features')
        with self.lock:self.latest=(float(sim_time),np.asarray(qpos).copy(),np.asarray(qvel).copy(),list(estimated_state),instruction)

    def read(self):
        with self.lock:return dict(self.result) if self.result else None

    def _render(self):
        import os
        os.environ.setdefault('MUJOCO_GL','egl')
        from rescue_scene import Camera
        camera=None
        try:
            camera=Camera(self.scene)
            if hasattr(camera,'provenance'):self.events.append(dict(event='camera_provenance',**camera.provenance))
            previous=None;frame_id=0
            while not self.stop.is_set():
                with self.lock:obs=self.latest
                if obs is None or obs[0]==previous:self.stop.wait(.005);continue
                sim_time,qpos,qvel,state,instruction=obs;previous=sim_time;start=time.monotonic()
                rgb=camera.render(qpos,qvel)
                stream=io.BytesIO();Image.fromarray(rgb).save(stream,format='JPEG',quality=70)
                frame=dict(frame_id=frame_id,sim_time_capture=sim_time,state=state,instruction=instruction,
                    jpeg=stream.getvalue(),capture_wall=start,render_ready_wall=time.monotonic())
                with self.lock:self.frame=frame
                frame_id+=1
        except BaseException as exc:
            self.events.append(dict(event='render_error',error=repr(exc)));self.stop.set()
        finally:
            if camera is not None:camera.close()

    def _run(self):
        try:
            with socket.socket() as listener:
                listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                listener.bind(('127.0.0.1',self.port));listener.listen(1);listener.settimeout(.5)
                self.events.append(dict(event='listening',port=self.port,pipeline='latest-frame-single-slot'))
                while not self.stop.is_set():
                    try:connection,_=listener.accept()
                    except socket.timeout:continue
                    self.events.append(dict(event='worker_connected'))
                    with connection:
                        connection.settimeout(20);sequence=0;previous_frame=None
                        while not self.stop.is_set():
                            with self.lock:frame=self.frame
                            if frame is None or frame['frame_id']==previous_frame:self.stop.wait(.005);continue
                            previous_frame=frame['frame_id'];jpeg=frame['jpeg'];image_file=None
                            if self.recording_directory:
                                image_file=f'{sequence:05d}.jpg'
                                with (self.recording_directory/image_file).open('xb') as f:f.write(jpeg)
                            begin=time.monotonic()
                            request=dict(version=1,id=sequence,sim_time_capture=frame['sim_time_capture'],
                                rgb_jpeg_base64=base64.b64encode(jpeg).decode(),state=frame['state'],instruction=frame['instruction'])
                            send(connection,request);response=receive(connection);end=time.monotonic()
                            action=np.asarray(response.get('action'),dtype=float)
                            if response.get('id')!=sequence or action.shape!=(6,) or not np.isfinite(action).all():raise ValueError('Invalid VLA response')
                            result=dict(id=sequence,sim_time_capture=frame['sim_time_capture'],instruction=frame['instruction'],
                                action=action.tolist(),wall_exchange_s=end-frame['capture_wall'],
                                inference_s=response.get('inference_s'),policy_kind=response.get('policy_kind','unknown'),
                                checkpoint_sha256=response.get('checkpoint_sha256'),action_chunk=response.get('action_chunk'),
                                action_dt_s=response.get('action_dt_s'),num_steps=response.get('num_steps'),perception=response.get('perception',{}),
                                image_file=image_file,image_sha256=hashlib.sha256(jpeg).hexdigest(),estimated_state=frame['state'],
                                pipeline_frame_id=frame['frame_id'],render_wall_s=frame['render_ready_wall']-frame['capture_wall'],
                                frame_queue_wall_s=begin-frame['render_ready_wall'],worker_exchange_wall_s=end-begin,
                                pipeline='latest-frame-single-slot')
                            with self.lock:self.result=result
                            self.events.append(dict(event='inference',**result));sequence+=1
        except BaseException as exc:self.events.append(dict(event='link_error',error=repr(exc)))
        finally:self.stop.set()

    def close(self):
        self.stop.set();self.thread.join(timeout=2);self.render_thread.join(timeout=2)
