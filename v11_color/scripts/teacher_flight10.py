"""Training-only tighter yaw targets; all other train09 targets preserved."""
import math
import numpy as np
from teacher_flight09 import teacher_chunk as previous_teacher

YAW_DEADBAND_RAD=.03
YAW_GAIN=.8

def teacher_chunk(task,qpos,own,targets,rotation,scale,steps=32):
    chunk=previous_teacher(task,qpos,own,targets,rotation,scale,steps)
    if task in [4,5] and own[8]>.5 and own[3]>.8:
        yaw=float(own[6]);target=math.pi/2 if task==4 else -math.pi/2
        for k in range(steps):
            error=target-yaw
            rate=0. if abs(error)<YAW_DEADBAND_RAD else float(np.clip(YAW_GAIN*error,-.35,.35))
            chunk[k,3]=rate/scale[3]
            yaw+=.1*rate
    return chunk
