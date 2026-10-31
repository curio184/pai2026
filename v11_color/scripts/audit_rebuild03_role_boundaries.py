"""Narrow AST and source checks, plus explicit limits of this review."""
import ast,datetime,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1];R=W/'runtime_rebuild03'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tree(name):return ast.parse((R/name).read_text(encoding='utf-8'))
def main():
    plan=json.loads((W/'protocol/rebuild03_final.json').read_text(encoding='utf-8'))
    for n,h in plan['runtime_sha256'].items():assert sha(R/n)==h
    worker=tree('search_worker.py')
    calls=[n for n in ast.walk(worker) if isinstance(n,ast.Call)]
    infer=[n for n in calls if ast.unparse(n.func)=='policy.infer_chunk']
    assert len(infer)==1 and [ast.unparse(a) for a in infer[0].args]==['rgb',"request['instruction']","request['state']"]
    detect=[n for n in calls if ast.unparse(n.func)=='perception.detect']
    assert len(detect)==1 and [ast.unparse(a) for a in detect[0].args]==['rgb']
    assert infer[0].lineno<detect[0].lineno
    decoder=tree('plan_endpoint.py');fn=next(n for n in decoder.body if isinstance(n,ast.FunctionDef))
    assert [a.arg for a in fn.args.args]==['chunk','own']
    imports={n.names[0].name for n in decoder.body if isinstance(n,ast.Import)}
    assert imports=={'math','numpy'}
    tracker=tree('plan_tracker.py');keys=set()
    for n in ast.walk(tracker):
        if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='packet':keys.add(ast.literal_eval(n.slice))
    assert keys=={'id','sim_time_capture','action_chunk','estimated_state'}
    transport=tree('pipelined_camera.py')
    req=[n.value for n in ast.walk(transport) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='request' for t in n.targets)]
    assert len(req)==1 and {x.arg for x in req[0].keywords}=={'version','id','sim_time_capture','rgb_jpeg_base64','state','instruction'}
    m=tree('search_mission.py')
    update=[n for n in ast.walk(m) if isinstance(n,ast.Call) and ast.unparse(n.func)=='plan_tracker.update']
    assert len(update)==1 and [ast.unparse(a) for a in update[0].args]==['t','own_state','att.yaw','model_action','model_packet','action_source','phase','prompt']
    own=[n for n in ast.walk(m) if isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id=='own_state' for a in n.targets)]
    assert len(own)==2
    assert sum(isinstance(n.value,ast.Constant) and n.value.value is None for n in own)==1
    features=next(n.value for n in own if isinstance(n.value,ast.List))
    assert len(features.elts)==9 and 'state[' not in ast.unparse(features)
    def excerpt(name,first,last):
        lines=(R/name).read_text(encoding='utf-8').splitlines()
        return dict(path=f'runtime_rebuild03/{name}',sha256=sha(R/name),first_line=first,last_line=last,text='\n'.join(lines[first-1:last]))
    result=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),narrow_checks_passed=True,
      runtime_hashes_match=True,policy_inputs=['RGB','stage English instruction','own estimated state'],
      decoder_inputs=['VLA action chunk','captured own estimated state'],tracker_packet_fields=sorted(keys),
      source_evidence=[excerpt('search_worker.py',46,55),excerpt('search_mission.py',234,267),excerpt('plan_endpoint.py',1,34),excerpt('plan_tracker.py',1,66)],
      manual_review=['Own velocity and attitude are read from MAVLink LOCAL_POSITION_NED and ATTITUDE. Physics truth supplies sensors/rendering and postflight logs.',
        'Person detector confirms discovery and loss; it does not supply navigation vectors to VLA or the plan tracker.',
        'Endpoint reconstruction uses known training action semantics. It is an action conversion and feedback controller, not unchanged raw-action execution.'],
      limits=['Named boundaries and source review only; not a complete formal information-flow proof.','No assertion that perception is always correct or that these checks alone prove task success.'])
    out=W/'reports/rebuild03_role_source_audit.json';assert not out.exists();out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(narrow_checks_passed=True,output=str(out))))
if __name__=='__main__':main()
