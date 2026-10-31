"""Record source evidence for role boundaries; no inference, flight, or mutation.

Checks narrow AST facts and source hashes. This is not a general information-flow
proof. The source excerpts support the accompanying manual implementation review.
"""
import ast, datetime, hashlib, json
from pathlib import Path

W=Path(__file__).resolve().parents[1]

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    lock=read(W/'protocol/runtime_english_lock.json')
    for name,expected in lock['runtime'].items():
        assert sha(W/'runtime_english'/name)==expected, name
    for name,expected in lock['project_imports'].items():
        assert sha(W.parent/name)==expected, name
    root=W/'runtime_english'
    worker=(root/'search_worker.py').read_text(encoding='utf-8')
    tree=ast.parse(worker)
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
    inference=[n for n in calls if ast.unparse(n.func)=='policy.infer_chunk']
    assert len(inference)==1
    assert [ast.unparse(x) for x in inference[0].args]==["rgb", "request['instruction']", "request['state']"]
    assert not inference[0].keywords
    detection=[n for n in calls if ast.unparse(n.func)=='perception.detect']
    assert len(detection)==1 and [ast.unparse(x) for x in detection[0].args]==['rgb']
    transport=ast.parse((root/'search_link.py').read_text(encoding='utf-8'))
    requests=[n.value for n in ast.walk(transport) if isinstance(n,ast.Assign)
              and any(isinstance(t,ast.Name) and t.id=='request' for t in n.targets)]
    assert len(requests)==1 and isinstance(requests[0],ast.Call)
    fields={k.arg:ast.unparse(k.value) for k in requests[0].keywords}
    assert set(fields)=={'version','id','sim_time_capture','rgb_jpeg_base64','state','instruction'}
    assert fields['state']=='state' and fields['instruction']=='instruction'
    policy=ast.parse((root/'smolvla_policy.py').read_text(encoding='utf-8'))
    batch=next(n for n in ast.walk(policy) if isinstance(n,ast.FunctionDef) and n.name=='batch')
    returned=[n.value for n in ast.walk(batch) if isinstance(n,ast.Return)]
    assert len(returned)==1 and isinstance(returned[0],ast.Dict)
    batch_fields=[ast.literal_eval(k) for k in returned[0].keys]
    assert set(batch_fields)=={'observation.images.camera1','observation.state',
                              'observation.language.tokens','observation.language.attention_mask'}
    def excerpt(name,start,end):
        path=root/name;lines=path.read_text(encoding='utf-8').splitlines()
        assert 0<start<=end<=len(lines)
        return dict(path=path.relative_to(W).as_posix(),sha256=sha(path),
                    first_line=start,last_line=end,text='\n'.join(lines[start-1:end]))
    evidence=[
        dict(claim='上位の青・赤の指示は定義済みの任務選択。VLAには英語の工程指示を渡す。',
             sources=[excerpt('search_mission.py',31,35),excerpt('search_mission.py',122,142)]),
        dict(claim='機体状態はMAVLinkの推定速度・姿勢などから作り、任務管理は発見確認や工程の継続時間を扱う。',
             sources=[excerpt('search_mission.py',225,248),excerpt('search_mission.py',269,341)]),
        dict(claim='画像・工程指示・9成分の機体状態がVLA入力。人物検出結果や正解の人物位置はこの入力に含まれない。',
             sources=[excerpt('search_link.py',87,109),excerpt('search_worker.py',51,59),excerpt('smolvla_policy.py',46,76)]),
        dict(claim='検出器は同じ画像から人物と服色を判定し、独立した確認処理が直近の異なる3画像で発見を確認する。',
             sources=[excerpt('perception.py',12,47),excerpt('confirmation.py',1,29)]),
        dict(claim='動作列の選択・鮮度確認・速度上限・離着陸要求の確認後、速度誤差を姿勢目標に変換してArduPilotに送る。',
             sources=[excerpt('search_link.py',130,189),excerpt('search_mission.py',248,268)]),
    ]
    report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        narrow_ast_checks_passed=True,checked_runtime_files=len(lock['runtime']),
        checked_project_imports=len(lock['project_imports']),runtime_lock_sha256=sha(W/'protocol/runtime_english_lock.json'),
        policy_call_arguments=[ast.unparse(x) for x in inference[0].args],
        detector_call_arguments=['rgb'],transport_fields=fields,policy_batch_fields=batch_fields,
        source_review=evidence,
        limits=['AST checks cover named call boundaries, not every possible information-flow path.',
                'Simulator truth is legitimately used for rendering, sensor synthesis, teacher labels and postflight scoring.',
                'Role separation does not guarantee correct detections, safe flight, or task completion.',
                'This source audit is not evidence that the current candidate meets its flight gates.'])
    dest=W/'reports/runtime_role_source_audit.json';assert not dest.exists()
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(report=str(dest),narrow_ast_checks_passed=True,source_claims=len(evidence))))

if __name__=='__main__':main()
