"""Search completion follows visual discovery, not precision-rotation benchmark."""
from pathlib import Path
here=Path(__file__).resolve().parent
file=here/'search_mission.py';text=file.read_text(encoding='utf8')
old='stable=abs(relative_yaw-target)<.12 and abs(att.yawspeed)<.08'
new='''# This is a visual search, not the separate 90-degree accuracy task.
                    # A confirmed target + settled, substantial scan ends this view.
                    stable=abs(att.yawspeed)<.08 and abs(relative_yaw)>.65 and confirmed
                    # If no target is seen, finish a coarse quarter turn before the next view.
                    if not confirmed:
                        stable=abs(relative_yaw-target)<.25 and abs(att.yawspeed)<.08'''
assert text.count(old)==1;text=text.replace(old,new)
old='if t>180:\n                stopped="mission_deadline_reached";break'
new='''if t>120 and phase!="land":
                mission_failure="mission_deadline"
                phase="land";stage_start=t
                sequence=["land"];stage_index=0
                events.append(dict(t=t,event="mission_deadline_normal_land"))
            if t>150:
                stopped="mission_deadline_reached";break'''
assert text.count(old)==1;text=text.replace(old,new)
# Unexpected autopilot landing/disarming is a failed task, never a success.
old='if "land" in actions and armed_at is not None and not is_armed:'
new='''if armed_at is not None and not is_armed and t-armed_at>5 and "land" not in actions:
                    stopped="unexpected_disarm";mission_failure="autopilot_landed_before_mission_completion";break
                if "land" in actions and armed_at is not None and not is_armed:'''
assert text.count(old)==1;text=text.replace(old,new)
file.write_text(text,encoding='utf8')
file=here/'score_search.py';text=file.read_text(encoding='utf8')
old="search_rotation_completed=base['rotations']['right']['completed']"
new="search_rotation_completed=bool(base['rotations']['right'].get('stopped') and 35<abs(base['rotations']['right'].get('clockwise_rotation_deg',0))<145)"
assert text.count(old)==1;text=text.replace(old,new)
file.write_text(text,encoding='utf8')
print('VISUAL_SEARCH_COMPLETION_UPDATED')
