"""Register the remaining existing conditions before the expanded development batch."""
import json,hashlib,datetime
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    base=read(W/'protocol/rebuild01_dev.json');previous=read(W/'protocol/navfocus_receipt.json')
    exclude={c['id'] for c in base['cases']}
    cases=[c for c in previous['cases'] if c['model']=='v1.1' and c['id'] not in exclude]
    assert len(cases)==23
    for c in cases:c['original_group']=c['group'];c['group']='development_existing_conditions'
    runner=(W/'scripts/run_suite_rebuild01.py').read_text(encoding='utf-8').replace('rebuild01_dev.json','rebuild01_expanded.json')
    dest=W/'scripts/run_suite_rebuild01_expanded.py';dest.write_text(runner,encoding='utf-8')
    plan={**base,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope':'Remaining23 existing v1.1 conditions as development. Starts only after all first3 pass. No fresh final evaluation results used.',
        'cases':cases,'initial_three_protocol_sha256':sha(W/'protocol/rebuild01_dev.json'),
        'runner_sha256':sha(dest),'model_and_runtime_changed':False}
    with (W/'protocol/rebuild01_expanded.json').open('x',encoding='utf-8') as f:json.dump(plan,f,indent=2)
    print(json.dumps(dict(cases=len(cases),same_runtime=True)))
if __name__=='__main__':main()
