"""Lock the new training code and unchanged bounded evaluation before training."""
import ast,datetime,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (W/'models/train09_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
plan=W/'protocol/train09_english.json';audit=W/'data/dataset09_en/audit.json'
assert read(audit)['plan_sha256']==sha(plan)
assert read(plan)['bounded_execution_protocol_sha256']==sha(W/'protocol/bounded_execution.json')
old=read(W/'protocol/train05_english_implementation.json')
common=[n for n in old['scripts'] if not any(t in n for t in ['train05','dataset05','training05'])]
for n in common:assert sha(W/'scripts'/n)==old['scripts'][n],n
bounded=read(W/'protocol/bounded_execution.json')
for n,h in bounded['scripts'].items():assert sha(W/'scripts'/n)==h,n
names=['train09_en.py','build_dataset09_en.py','register_train09_en.py','teacher_flight09.py','teacher_flight08.py',
    'preflight_train09_loss.py','pipeline_train09_en.py','report_bounded_execution.py',
    'run_round02_bounded.py','run_suite_bounded.py','bounded_wsl.py','bounded_wsl_entry.py']+common
for n in names:ast.parse((W/'scripts'/n).read_text(encoding='utf-8-sig'))
obj=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(plan),
    trainer_sha256=sha(W/'scripts/train09_en.py'),dataset_audit_sha256=sha(audit),
    runtime_lock_sha256=sha(W/'protocol/runtime_english_lock.json'),
    bounded_execution_protocol_sha256=sha(W/'protocol/bounded_execution.json'),
    scripts={n:sha(W/'scripts'/n) for n in names},training_started=False,final_evaluation_started=False)
out=W/'protocol/train09_english_implementation.json';assert not out.exists()
out.write_text(json.dumps(obj,indent=2),encoding='utf8')
print(json.dumps(dict(implementation_sha256=sha(out),scripts=len(obj['scripts']))))
