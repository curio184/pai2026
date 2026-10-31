"""Training-only mild stationary braking; every navigation target is preserved."""
import numpy as np
from teacher_flight14 import teacher_chunk as previous_teacher
BRAKING_COEFFICIENT=.6

def teacher_chunk(task,qpos,own,targets,rotation,scale,steps=32):
    chunk=previous_teacher(task,qpos,own,targets,rotation,scale,steps)
    if task in [2,4,5,6]:
        brake=np.zeros(2)
        if own[8]>.5 and not (task==2 and own[3]<.25):
            brake=-BRAKING_COEFFICIENT*np.asarray(own[:2],dtype=float)
            speed=np.linalg.norm(brake)
            if speed>.2:brake*=.2/speed
        chunk[:,:2]=brake/np.asarray(scale[:2])
    return chunk
