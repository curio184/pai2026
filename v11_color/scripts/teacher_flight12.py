"""Training-only stronger braking and latency-aware yaw targets."""
import math
import numpy as np
from teacher_flight10 import teacher_chunk as previous_teacher
BRAKING_COEFFICIENT=1.2
YAW_DEADBAND_RAD=.03
YAW_GAIN=.8
YAW_CAP_RAD_S=.25
YAW_CAPTURE_LOOKAHEAD_S=1.0
def teacher_chunk(task,qpos,own,targets,rotation,scale,steps=32):
    chunk=previous_teacher(task,qpos,own,targets,rotation,scale,steps)
    if task in [2,4,5,6]:
        brake=np.zeros(2)
        if own[8]>.5 and not (task==2 and own[3]<.25):
            brake=-BRAKING_COEFFICIENT*np.asarray(own[:2],dtype=float)
            speed=np.linalg.norm(brake)
            if speed>.2:brake*=.2/speed
        chunk[:,:2]=brake/np.asarray(scale[:2])
    if task in [4,5] and own[8]>.5 and own[3]>.8:
        yaw=float(own[6])+YAW_CAPTURE_LOOKAHEAD_S*float(own[7])
        target=math.pi/2 if task==4 else -math.pi/2
        for k in range(steps):
            error=target-yaw
            rate=0. if abs(error)<YAW_DEADBAND_RAD else float(np.clip(YAW_GAIN*error,-YAW_CAP_RAD_S,YAW_CAP_RAD_S))
            chunk[k,3]=rate/scale[3];yaw+=.1*rate
    return chunk
