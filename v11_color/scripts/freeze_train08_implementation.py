"""Lock training/evaluation code after data preparation, before preflight/training."""
import ast,datetime,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
assert not (W/'models/train08_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
plan=W/'protocol/train08_english.json';audit=W/'data/dataset08_en/audit.json'
assert read(audit)['plan_sha256']==sha(plan)
old=read(W/'protocol/train05_english_implementation.json')
common=[n for n in old['scripts'] if not any(t in n for t in ['train05','dataset05','training05'])]
for n in common:assert sha(W/'scripts'/n)==old['scripts'][n],n
names=['train08_en.py','build_dataset08_en.py','register_train08_en.py','teacher_flight08.py',
       'preflight_train08_loss.py','pipeline_train08_en.py']+common
for n in names:ast.parse((W/'scripts'/n).read_text(encoding='utf-8-sig'))
obj=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(plan),
    trainer_sha256=sha(W/'scripts/train08_en.py'),dataset_audit_sha256=sha(audit),
    runtime_lock_sha256=sha(W/'protocol/runtime_english_lock.json'),
    scripts={n:sha(W/'scripts'/n) for n in names},training_started=False,final_evaluation_started=False)
out=W/'protocol/train08_english_implementation.json';assert not out.exists()
out.write_text(json.dumps(obj,indent=2),encoding='utf-8')
print(json.dumps(dict(implementation_sha256=sha(out),trainer_sha256=obj['trainer_sha256'],dataset_audit_sha256=obj['dataset_audit_sha256'],scripts=len(names))))
