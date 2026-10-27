from pathlib import Path
here=Path(__file__).resolve().parent
source=(here/'perception.py').read_text(encoding='utf8')
(here/'confirmation.py').write_text(source[source.index('class VisualConfirmation:'):],encoding='utf8')
file=here/'search_mission.py';text=file.read_text(encoding='utf8')
def replace(a,b):
    global text
    assert text.count(a)==1,a
    text=text.replace(a,b)
replace('out = args.output','''commands={"青い服の人を探して":"blue", "赤い服の人を探して":"red"}
    if args.instruction is not None:
        if args.instruction not in commands: raise ValueError("Supported commands: "+str(list(commands)))
        args.profile=commands[args.instruction]
    out = args.output''')
replace('instructions["report"]=instructions["hover"]','instructions["report"]=instructions["hover"]\n    instructions["reacquire"]=instructions["hover"]')
replace('mission_failure=None','mission_failure=None\n    search_start_observation=None\n    resume_phase=None')
replace('prompt=instructions[phase]','''if phase in (args.profile,"report") and visual.last_seen is not None and t-visual.last_seen>3.0:
                    resume_phase=phase
                    sequence[stage_index:stage_index]=["reacquire"]
                    stage_history.append(dict(phase=phase,start=stage_start,end=t,interrupted="visual_target_lost"))
                    phase="reacquire";stage_start=t;settled_since=None;stop_window.reset()
                    events.append(dict(t=t,event="visual_target_lost_hover"))
                prompt=instructions[phase]''')
replace('elif phase in ("hover","confirm","report"):','elif phase in ("hover","confirm","report","reacquire"):')
replace('if phase=="report":\n                    stable=stable and confirmed','''if phase in ("report","reacquire"):
                    stable=stable and confirmed
                if phase=="reacquire" and t-stage_start>12:
                    mission_failure="target_lost_after_discovery"
                    sequence[stage_index+1:]=["land"]
                    navigation_complete=True''')
replace('if phase=="confirm" and not mission_failure:', '''if phase=="hover":
                        search_start_observation=dict(id=model_packet['id'],t=model_packet['sim_time_capture'],
                            image_file=model_packet['image_file'],image_sha256=model_packet['image_sha256'],
                            perception=model_packet.get('perception',{}),estimated_state=own_state)
                        (out/"search_start_observation.json").write_text(json.dumps(search_start_observation,indent=2),encoding="utf8")
                        events.append(dict(event="search_started",**search_start_observation))
                    if phase=="confirm" and not mission_failure:''')
replace('result = dict(upper_instruction=upper_instruction,','result = dict(search_start_observation=search_start_observation,upper_instruction=upper_instruction,')
replace('p.add_argument("--profile",choices=["blue","red"],default="blue")','p.add_argument("--profile",choices=["blue","red"],default="blue")\n    p.add_argument("--instruction",type=str)')
file.write_text(text,encoding='utf8')
file=here/'run_search.py';text=file.read_text(encoding='utf8')
replace("'--output',lp(out/name),'--profile',case['profile'],'--chunk-origin','split']", "'--output',lp(out/name),'--instruction',manifest['upper_command'],'--chunk-origin','split']")
file.write_text(text,encoding='utf8')
print('VISUAL_LOSS_AND_COMMAND_PATH_ADDED')
