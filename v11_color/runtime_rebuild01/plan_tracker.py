"""Track a VLA-generated endpoint with onboard odometry and explicit provenance.

Camera capture pose is reconstructed from estimated velocity/yaw history.
Only the VLA plan selects the endpoint. No person detection or simulator truth.
"""
from collections import deque
import math
import numpy as np
from plan_endpoint import decode_plan_endpoint

def rotation(yaw):
    c,s=math.cos(yaw),math.sin(yaw)
    return np.array([[c,s],[s,-c]])  # body forward/left to NED north/east

class PlanTracker:
    def __init__(self):
        self.position=np.zeros(2);self.history=deque();self.last_time=None
        self.instruction=None;self.last_id=None;self.target=None;self.decode=None;self.packet=None
        self.evidence=None

    def update(self,now,own,yaw,raw,packet,source,phase,instruction):
        own=np.asarray(own,dtype=float);r=rotation(yaw);action=np.asarray(raw,dtype=float).copy()
        if self.last_time is not None:
            dt=now-self.last_time
            assert 0<dt<=.11
            self.position+=dt*(r@own[:2])
        self.last_time=now;self.history.append((now,self.position.copy(),yaw))
        while len(self.history)>2 and self.history[1][0]<now-12:self.history.popleft()
        if instruction!=self.instruction:
            self.instruction=instruction;self.last_id=None;self.target=None;self.decode=None
        self.evidence=dict(owner='mission_primitive' if phase not in ['blue','red'] else 'VLA_plan_tracker',
            own_odometry_ned=self.position.tolist(),raw_selected_action=action.tolist(),truth_used=False)
        if phase not in ['blue','red']:return action,self.evidence
        if source!='policy' or packet is None:
            self.evidence['valid_plan']=False
            return action,self.evidence
        if packet['id']!=self.last_id:
            at=min(self.history,key=lambda x:abs(x[0]-packet['sim_time_capture']))
            assert abs(at[0]-packet['sim_time_capture'])<.11
            endpoint,decoded=decode_plan_endpoint(packet['action_chunk'],packet['estimated_state'])
            target=at[1]+rotation(at[2])@endpoint
            self.target=target if self.target is None else .5*self.target+.5*target
            self.decode=decoded;self.last_id=packet['id'];self.packet=packet
            self.capture=dict(time_s=at[0],odometry_ned=at[1].tolist(),yaw_ned=at[2],
                decoded_target_ned=target.tolist())
        error=r.T@(self.target-self.position)
        request=.8*error-.5*own[:2]
        norm=np.linalg.norm(request)
        if norm>.2:request*=.2/norm
        action[:2]=request
        ready=bool(self.decode['stop_planned'] and np.linalg.norm(error)<.08 and np.linalg.norm(own[:2])<.05)
        self.evidence.update(valid_plan=True,packet_id=self.last_id,packet_capture_s=self.packet['sim_time_capture'],
            capture=self.capture,decode=self.decode,filtered_target_ned=self.target.tolist(),
            remaining_forward_left_m=error.tolist(),tracking_request_forward_left=request.tolist(),
            stop_ready=ready,role='VLA chooses the plan endpoint; own-state tracking converts it to velocity. Raw plan retained.')
        return action,self.evidence
