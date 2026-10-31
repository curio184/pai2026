"""Freeze the user-approved single execution-origin change before any flight."""
import ast,datetime,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def create(p,text):
    with p.open('x',encoding='utf-8') as f:f.write(text)

def main():
    original=W/'protocol/navfocus_final.json';plan=read(original)
    before=(W/'scripts/run_suite_navfocus.py').read_text(encoding='utf-8')
    assert before.count("'--chunk-origin','split'")==1
    after=before.replace("'--chunk-origin','split'","'--chunk-origin','receipt'")
    after=after.replace("'protocol/navfocus_final.json'","'protocol/navfocus_receipt.json'")
    ast.parse(after);create(W/'scripts/run_suite_receipt.py',after)
    # The independent scorer and runtime stay byte-identical. Only runner,
    # destination/protocol, and verifier's source references differ.
    verify=(W/'scripts/verify_navfocus.py').read_text(encoding='utf-8')
    for a,b in [('protocol/navfocus_final.json','protocol/navfocus_receipt.json'),
                ('runs/navfocus_final','runs/navfocus_receipt'),('run_suite_navfocus.py','run_suite_receipt.py'),
                ('reports/navfocus_records_verified.json','reports/receipt_records_verified.json'),
                ('reports/navfocus_execution_audit.json','reports/receipt_execution_audit.json')]:verify=verify.replace(a,b)
    ast.parse(verify);create(W/'scripts/verify_receipt.py',verify)
    plan.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        deadline_utc='2026-10-30T16:19:29+00:00',configuration='navfocus_receipt',
        authorization='User explicitly approved receipt-origin change, one fixed42-flight validation, no training/gain/scoring changes, and up to150minutes including documents.',
        original_fixed_protocol_sha256=sha(original),
        only_runtime_argument_change={'before':['--chunk-origin','split'],'after':['--chunk-origin','receipt']},
        runtime_sources_changed=False,models_changed=False,scoring_changed=False,
        evaluation_disclosure='Same layouts and seeds as prior navfocus trials. Not used for training, but results informed execution-origin revision. Not an independent new holdout.',
        static_probe_reuse={'path':'probe_navfocus/outputs/summary.json','sha256':sha(W/'probe_navfocus/outputs/summary.json'),
                           'reason':'Identical model, image, instruction, state and inference. Execution-origin option affects flight only.'},
        scripts={n:sha(W/'scripts'/n) for n in ['run_suite_receipt.py','run_receipt_validation.py','verify_receipt.py',
                    'register_receipt_validation.py','score_navfocus.py','bounded_wsl.py','bounded_wsl_entry.py']})
    assert plan['cases']==read(original)['cases'] and len(plan['cases'])==42
    create(W/'protocol/navfocus_receipt.json',json.dumps(plan,ensure_ascii=False,indent=2))
    print(json.dumps({'protocol_sha256':sha(W/'protocol/navfocus_receipt.json'),'cases':42,'deadline_utc':plan['deadline_utc']}))
if __name__=='__main__':main()
