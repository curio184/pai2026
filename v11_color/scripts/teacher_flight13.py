"""Training-only navigation targets that keep the requested person centered.

Ground-truth geometry is available to this offline teacher only. Runtime inputs,
mission manager, controller, detector, and scoring are not modified.
"""
import math
import numpy as np
from teacher_flight12 import teacher_chunk as previous_teacher

NAVIGATION_YAW_GAIN=.8
NAVIGATION_YAW_DEADBAND_RAD=.05
NAVIGATION_YAW_CAP_RAD_S=.25

def teacher_chunk(task,qpos,own,targets,rotation,scale,steps=32):
    if task not in [0,1]:
        return previous_teacher(task,qpos,own,targets,rotation,scale,steps)
    p=np.asarray(qpos[:3],dtype=float).copy()
    r=rotation(qpos[3:]); heading=math.atan2(r[1,0],r[0,0])
    s=np.asarray(own,dtype=float).copy(); chunk=[]
    person=np.asarray(targets[['blue','red'][task]][:2],dtype=float)
    goal=person+[-1.,0.]
    for _ in range(steps):
        a=np.zeros(6)
        if s[8]<.5:
            a[4]=1.
        else:
            a[2]=np.clip(.7*(1-s[3]),-.3,.3)
            if s[3]>.8:
                c,ss=math.cos(heading),math.sin(heading)
                delta=goal-p[:2]
                if np.linalg.norm(delta)>.02:
                    a[:2]=np.array([[c,ss],[-ss,c]])@(1.4*delta)
                a[:2]-=.5*s[:2]
                norm=np.linalg.norm(a[:2])
                if norm>.2: a[:2]*=.2/norm
                toward=person-p[:2]
                bearing=math.atan2(toward[1],toward[0])-heading
                bearing=math.atan2(math.sin(bearing),math.cos(bearing))
                # Positive action yaw turns clockwise in the frozen runtime.
                a[3]=0. if abs(bearing)<NAVIGATION_YAW_DEADBAND_RAD else float(np.clip(-NAVIGATION_YAW_GAIN*bearing,-NAVIGATION_YAW_CAP_RAD_S,NAVIGATION_YAW_CAP_RAD_S))
        chunk.append(a/scale)
        if s[8]>.5:
            s[:2]+=.1*(a[:2]-s[:2])
            c,ss=math.cos(heading),math.sin(heading)
            world_velocity=np.array([[c,-ss],[ss,c]])@s[:2]
            p[:2]+=.1*world_velocity
            p[2]+=.1*a[2]; s[3]=p[2]
            s[6]+=.1*a[3]; s[7]=a[3]; heading-=.1*a[3]
            c,ss=math.cos(heading),math.sin(heading)
            s[:2]=np.array([[c,ss],[-ss,c]])@world_velocity
    return np.asarray(chunk,dtype=np.float32)
