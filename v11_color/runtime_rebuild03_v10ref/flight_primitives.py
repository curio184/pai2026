"""Own-state-only flight primitives; person-relative motion remains VLA-generated."""
import math
import numpy as np

def flight_action(phase, state, policy_action, source, time_s):
    s=np.asarray(state,dtype=float);raw=np.asarray(policy_action,dtype=float)
    assert s.shape==(9,) and raw.shape==(6,) and np.isfinite(s).all() and np.isfinite(raw).all()
    out=raw.copy()
    if time_s<16:return np.zeros(6),dict(owner='initialization',approach_unchanged=False)
    if source=='watchdog_land':return raw.copy(),dict(owner='watchdog',approach_unchanged=False)
    if phase in ('blue','red'):
        # Position, velocity, altitude and heading actions come from the VLA.
        # Arming/landing is an explicitly planned primitive, not a person choice.
        out[4:]=0
        return out,dict(owner='VLA',approach_unchanged=True,components_preserved=[0,1,2,3])
    out[:]=0
    armed=s[8]>.5
    if phase=='land':
        out[5]=float(armed)
        return out,dict(owner='mission_primitive',primitive='land',approach_unchanged=False)
    out[4]=float(phase=='takeoff' and not armed)
    out[2]=float(np.clip(.8*(1.-s[3])-.4*s[2],-.3,.3))
    if phase in ('right','left'):
        target=math.pi/2 if phase=='right' else -math.pi/2
        error=math.atan2(math.sin(target-s[6]),math.cos(target-s[6]))
        out[3]=0. if abs(error)<.03 and abs(s[7])<.03 else float(np.clip(.8*error-.4*s[7],-.25,.25))
    return out,dict(owner='mission_primitive',primitive=phase,approach_unchanged=False)
