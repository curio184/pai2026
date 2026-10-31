"""Supplement a missing source copy using its already preregistered digest."""
import datetime,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
planfile=W/'protocol/train13_english.json';plan=read(planfile)
preflight=read(W/'reports/train13_teacher_preflight_audit.json')
teacher=W/'scripts/teacher_flight13.py'
assert sha(teacher)==plan['teacher_source_sha256']==preflight['teacher_sha256']
assert sha(planfile)==preflight['plan_sha256']
assert sha(W/'data/dataset13_en/audit.json')==preflight['dataset_audit_sha256']
folder=W/'models/train13_en/source_snapshot_supplement';assert not folder.exists()
folder.mkdir();shutil.copy2(teacher,folder/teacher.name)
assert sha(folder/teacher.name)==sha(teacher)
report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,
    plan_sha256=sha(planfile),teacher_sha256=sha(teacher),copied_source=str(folder/teacher.name),
    issue='The original source_snapshot copied the inherited teacher12 dependencies but omitted teacher_flight13.py. The implementation manifest also omitted that direct teacher, although the preregistered plan and preflight audit independently pin its hash.',
    resolution='Supplemental copy matches both preregistered hashes. No original plan, implementation manifest, training data, model, or trial record is changed.',
    timing='This copy is made after training. Pre-training identity is evidenced by the preserved plan and preflight audit, not by the copy timestamp.')
(folder/'receipt.json').write_text(json.dumps(report,indent=2),encoding='utf8')
dest=W/'reports/train13_teacher_source_completion_audit.json';assert not dest.exists()
dest.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
