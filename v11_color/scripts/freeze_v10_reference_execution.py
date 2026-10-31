import datetime,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
names=['run_v10_teacher_reference.py','run_suite_rebuild03_v10ref.py','audit_v10_teacher_reference.py','score_rebuild03.py','bounded_wsl.py','bounded_wsl_entry.py']
out=W/'protocol/rebuild03_v10_reference_execution.json'
with out.open('x',encoding='utf-8') as f:
 json.dump(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(W/'protocol/rebuild03_v10_reference.json'),
   script_sha256={n:sha(W/'scripts'/n) for n in names},preflight_sha256=sha(W/'reports/rebuild03_v10_decoder_preflight.json'),
   note='Code/source provenance only; no change to previously registered cases, semantic coefficients or success conditions.'),f,indent=2)
print(out)
