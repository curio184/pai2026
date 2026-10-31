"""Decode the endpoint represented by a VLA velocity plan, in capture body FL.

Only generated actions and captured onboard velocity are inputs. No detector,
person coordinates, scene ID, language parsing or simulation truth.
The rollout matches the legacy v1.0 teacher action semantics (gain .7, no damping); it is not a physical score.
"""
import math
import numpy as np

def decode_plan_endpoint(chunk, own):
    chunk=np.asarray(chunk,dtype=float)
    v=np.asarray(own[:2],dtype=float).copy()
    p=np.zeros(2);h=0.;estimates=[]
    assert chunk.ndim==2 and chunk.shape[1]==6 and np.isfinite(chunk).all()
    for i,a in enumerate(chunk):
        c,s=math.cos(h),math.sin(h)
        r=np.array([[c,-s],[s,c]])
        # Unsaturated velocity labels contain an estimate of remaining motion.
        if i>=len(chunk)//2 and np.linalg.norm(a[:2])<.18:
            estimates.append(p+r@a[:2]/.7)
        v+=.1*(a[:2]-v)
        world_v=r@v
        p+=.1*world_v
        h-=.1*a[3]
        c,s=math.cos(h),math.sin(h)
        v=v  # Legacy teacher retains its simulated body-velocity components.
    endpoint=np.median(estimates,axis=0) if estimates else p
    return endpoint,dict(unsaturated_estimates=len(estimates),
        rollout_endpoint=p.tolist(), stop_planned=bool(np.mean(np.linalg.norm(chunk[-8:,:2],axis=1))<.04),
        endpoint_forward_left=endpoint.tolist())
