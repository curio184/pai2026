"""Training-only candidate teacher: mild horizontal braking for stationary phases.

Navigation and all nonhorizontal labels are inherited from the registered train08
teacher. No runtime controller change. Preregister before generating any dataset.
"""
import numpy as np
from teacher_flight08 import teacher_chunk as previous_teacher

BRAKING_COEFFICIENT = 0.6

def teacher_chunk(task,qpos,own,targets,rotation,scale,steps=32):
    chunk=previous_teacher(task,qpos,own,targets,rotation,scale,steps)
    if task in [2,4,5,6]:
        brake=np.zeros(2,dtype=float)
        if own[8]>.5 and not (task==2 and own[3]<.25):
            brake=-BRAKING_COEFFICIENT*np.asarray(own[:2],dtype=float)
            speed=np.linalg.norm(brake)
            if speed>.2:brake*=.2/speed
        chunk[:,:2]=brake/np.asarray(scale[:2])
    return chunk
