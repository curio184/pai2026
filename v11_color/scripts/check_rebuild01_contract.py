"""Preflight semantics: teacher decoding, FL/NED signs, delayed pose compensation."""
import sys,json,math,hashlib,datetime
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(W/'runtime_rebuild01'))
from plan_endpoint import decode_plan_endpoint
from plan_tracker import PlanTracker,rotation
from teacher_flight16 import teacher_chunk
def main():
    rows=[]
    for dx,dy,vx,vy in [( .3,.2,.1,-.05),(-.2,.2,0.,0.),(.05,-.05,0.,0.),(.8,.2,0.,0.)]:
        own=np.array([vx,vy,0,1,0,0,0,0,1.]);goal=np.array([dx,dy]);person=np.r_[goal+[1.,0],0]
        chunk=teacher_chunk(0,np.array([0,0,1,1,0,0,0.]),own,{'blue':person},lambda q:np.eye(3),np.ones(6))
        endpoint,details=decode_plan_endpoint(chunk,own)
        error=float(np.linalg.norm(endpoint-goal))
        if details['unsaturated_estimates']:assert error<.025,(goal,endpoint)
        rows.append(dict(goal=goal.tolist(),error=error,**details))
    assert np.allclose(rotation(0)@[1,0],[1,0])
    assert np.allclose(rotation(math.pi/2)@[1,0],[0,1])
    assert np.allclose(rotation(0)@[0,1],[0,-1])
    tracker=PlanTracker();own=np.array([.1,0,0,1,0,0,0,0,1.])
    for i in range(21):tracker.update(i*.05,own,0,np.zeros(6),None,'awaiting_policy','blue','blue')
    packet=dict(id=1,sim_time_capture=.5,estimated_state=own.tolist(),action_chunk=chunk.tolist())
    action,e=tracker.update(1.05,own,0,np.zeros(6),packet,'policy','blue','blue')
    delta,_=decode_plan_endpoint(chunk,own)
    expected=e['capture']['odometry_ned']+rotation(0)@delta
    assert np.allclose(e['filtered_target_ned'],expected)
    assert abs(e['own_odometry_ned'][0]-.105)<1e-10
    assert np.allclose(e['raw_selected_action'],np.zeros(6))
    assert e['truth_used'] is False
    result=dict(passed=True,teacher_endpoint_checks=rows,coordinate_signs_passed=True,
        capture_odometry_compensation_passed=True,no_flight=True,no_policy_inference=True,
        limitations='Does not prove closed-loop flight success.',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    with (W/'reports/rebuild01_preflight.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
if __name__=='__main__':main()
