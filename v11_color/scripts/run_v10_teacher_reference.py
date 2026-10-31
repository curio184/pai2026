import datetime,json
from run_suite_rebuild03_v10ref import W,P,sha,write,run_case,lock_check
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    # No overlapping flight or inference; only after the original full batch.
    assert read(W/'runs/rebuild03_final/summary.json')['completed']==42
    assert (W/'probe_rebuild03/outputs/summary.json').exists()
    plan=read(W/'protocol/rebuild03_v10_reference.json')
    execution=read(W/'protocol/rebuild03_v10_reference_execution.json')
    assert sha(W/'protocol/rebuild03_v10_reference.json')==execution['plan_sha256']
    for name,digest in execution['script_sha256'].items():assert sha(W/'scripts'/name)==digest
    assert sha(W/'reports/rebuild03_v10_decoder_preflight.json')==execution['preflight_sha256']
    assert sha(W/'scripts/run_suite_rebuild03_v10ref.py')==plan['runner_sha256']
    checkpoint=P/read(W/'protocol/plan.json')['training']['initial_checkpoint']
    assert sha(checkpoint/'model.safetensors')==plan['checkpoint_sha256']
    root=W/'runs/rebuild03_v10_reference';root.mkdir(exist_ok=False)
    outcomes=[]
    for case in plan['cases']:
        lock_check()
        status=dict(stage='teacher_semantics_reference',case=case['id'],completed=len(outcomes),planned=16,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        write(W/'rebuild10h_status.json',status);print(json.dumps(status),flush=True)
        out=run_case(case,checkpoint,root/(case['id']+'_'+case['model']));outcomes.append(out)
        write(root/'summary.json',dict(cases=outcomes,completed=len(outcomes),planned=16))
        if out.get('error'):raise RuntimeError(out)
    print('REFERENCE_COMPLETE',flush=True)
if __name__=='__main__':main()
