"""Build the separately authorized architecture once, before flight evaluation."""
import ast,hashlib,json,shutil,datetime
from pathlib import Path
W=Path(__file__).resolve().parents[1];P=W.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    old=W/'runtime_control_v11';new=W/'runtime_navfocus';lock=read(W/'protocol/runtime_control_v11_lock.json')
    assert not new.exists()
    assert all(sha(old/n)==h for n,h in lock['runtime'].items())
    shutil.copytree(old,new,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copyfile(W/'scripts/flight_primitives_navfocus.py',new/'flight_primitives.py')
    for name in ['search_mission.py','ardupilot_bridge/rescue_mission.py']:
        file=new/name;s=file.read_text(encoding='utf-8')
        s=s.replace('from velocity_stabilizer import HorizontalVelocityStabilizer','from velocity_stabilizer import HorizontalVelocityStabilizer\nfrom flight_primitives import flight_action')
        s=s.replace('horizontal_control=None','horizontal_control=None\n    adopted_action=np.zeros(6);execution_owner=None')
        needle='                if model_action[4]>0:'
        assert needle in s
        s=s.replace(needle,'                adopted_action,execution_owner=flight_action(phase,own_state,model_action,action_source,t)\n'+needle.replace('model_action','adopted_action'))
        s=s.replace('event="policy_takeoff_request"','event="mission_takeoff_request",source="mission_primitive"')
        s=s.replace('if model_action[5]>0 and "land" not in actions:','if adopted_action[5]>0 and "land" not in actions:')
        s=s.replace('event="land_request",source=action_source','event="land_request",source="watchdog_land" if action_source=="watchdog_land" else "mission_primitive"')
        s=s.replace('yaw_target+=float(model_action[3])*control_dt','yaw_target+=float(adopted_action[3])*control_dt')
        s=s.replace('thrust=.5+float(model_action[2])/(2*(1.0 if model_action[2]>=0 else .5))','thrust=.5+float(adopted_action[2])/(2*(1.0 if adopted_action[2]>=0 else .5))')
        # A larger settling margin does not relax any independent physical criterion.
        s=s.replace('t-settled_since>3.25','t-settled_since>5.0')
        transition='                    stage_history.append(dict(phase=phase,start=stage_start,end=t))'
        assert transition in s
        s=s.replace(transition,'                    if phase in ("blue","red") and navigation_complete:\n                        events.append(dict(t=t,event="vla_approach_completed",phase=phase,source=action_source,stop_intent=stop_window.evidence,model_packet_id=model_packet["id"] if model_packet else None))\n'+transition)
        s=s.replace('stop_window.reset()\n                    events.append(dict(t=t,event="instruction_changed",phase=phase))','stop_window.reset();yaw_target=att.yaw\n                    events.append(dict(t=t,event="instruction_changed",phase=phase))')
        s=s.replace('horizontal_control=horizontal_control,stop_intent_evidence=stop_window.evidence,','horizontal_control=horizontal_control,stop_intent_evidence=stop_window.evidence,\n                                 adopted_action=adopted_action.tolist(),execution_owner=execution_owner,')
        s=s.replace('controller_source_modified=False,','controller_source_modified=False,flight_adapter_revision="navfocus",')
        ast.parse(s);file.write_text(s,encoding='utf-8')
    entries={p.relative_to(new).as_posix():sha(p) for p in new.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    obj=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_lock_sha256=sha(W/'protocol/runtime_control_v11_lock.json'),
      authorization='User explicitly approved conventional takeoff/fixed-angle turn/landing and a new fixed validation; VLA retains person choice and approach/deceleration/stop. No training or physical acceptance relaxation.',
      runtime=entries,project_imports=lock['project_imports'],
      boundary='During approach, all four continuous VLA channels are unchanged. During non-approach phases ordinary own-state control executes planned primitives; all raw and adopted actions are logged.',
      gains='One analytically specified configuration, no gain search: own-altitude P .8, vertical damping .4; own-relative-yaw P .8, yaw damping .4, cap .25rad/s and .03rad settling deadband; horizontal PI unchanged.',
      scoring='Physical criteria unchanged. Command provenance must acknowledge mission primitives, not falsely label them VLA outputs. Original provenance-based score will be retained alongside the new score; approach completion additionally requires fresh VLA stop intent.')
    (W/'protocol/runtime_navfocus_lock.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(files=len(entries),runtime_lock_sha256=sha(W/'protocol/runtime_navfocus_lock.json'))))
if __name__=='__main__':main()
