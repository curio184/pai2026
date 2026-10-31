"""Training-only teacher; the runtime controller and scorer are unchanged."""
import math
import numpy as np

def teacher_chunk(task,qpos,own,targets,rotation,scale,steps=32):
    p=qpos[:3].astype(float).copy()
    r=rotation(qpos[3:]); heading=math.atan2(r[1,0],r[0,0])
    s=own.astype(float).copy(); chunk=[]
    for _ in range(steps):
        a=np.zeros(6)
        if task==3:a[5]=float(s[8]>.5)
        elif s[8]<.5:a[4]=float(task in [0,1,2])
        else:
            a[2]=np.clip(.7*(1-s[3]),-.3,.3)
            if task in [0,1] and s[3]>.8:
                delta=targets[['blue','red'][task]][:2]+[-.9,0]-p[:2]
                if np.linalg.norm(delta)>.02:
                    c,ss=math.cos(heading),math.sin(heading)
                    a[:2]=np.array([[c,ss],[-ss,c]])@(1.4*delta)
                a[:2]-=.5*s[:2]
                norm=np.linalg.norm(a[:2])
                if norm>.2:a[:2]*=.2/norm
            if task in [4,5] and s[3]>.8:
                error=(math.pi/2 if task==4 else -math.pi/2)-s[6]
                a[3]=0 if abs(error)<.12 else np.clip(.8*error,-.35,.35)
        chunk.append(a/scale)
        if s[8]>.5 and task!=3:
            s[:2]+=.1*(a[:2]-s[:2])
            c,ss=math.cos(heading),math.sin(heading)
            p[:2]+=.1*(np.array([[c,-ss],[ss,c]])@s[:2])
            p[2]+=.1*a[2];s[3]=p[2]
            s[6]+=.1*a[3];s[7]=a[3];heading-=.1*a[3]
    return np.asarray(chunk,dtype=np.float32)
