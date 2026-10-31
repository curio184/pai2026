"""Prepare code only; do not register, generate data, train, or fly."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
for old,new in [('train08_en.py','train09_en.py'),('preflight_train08_loss.py','preflight_train09_loss.py'),('pipeline_train08_en.py','pipeline_train09_en.py')]:
    out=W/'scripts'/new;assert not out.exists()
    source=(W/'scripts'/old).read_text(encoding='utf8').replace('train08','train09').replace('Train08','Train09').replace('dataset08','dataset09').replace('teacher_flight08','teacher_flight09').replace('pipeline08_en_','pipeline09_en_')
    if new=='train09_en.py':
        source=source.replace('Horizontal teacher relabeled to zero hold targets and sharper navigation with a 10cm teacher safety margin; no new state anchors.',
            'Stationary horizontal teacher relabeled to mild -0.6 captured-velocity braking; grounded takeoff zero. Navigation and all nonhorizontal labels preserved; no new inputs.')
        source=source.replace("W/'scripts/teacher_flight09.py',W/'protocol/storage_migration_e.json'", "W/'scripts/teacher_flight09.py',W/'scripts/teacher_flight08.py',W/'protocol/storage_migration_e.json'")
    if new=='pipeline_train09_en.py':
        source=source.replace("'run_round02_english.py'","'run_round02_bounded.py'")
        source=source.replace("status(stage,state='running')","status(stage,state='running',resources='4 CPUs / 8GiB / nice 10 / one flight at a time')")
        source=source.replace("py('verified_summary','summarize_round02_english.py','--candidate',CANDIDATE)","py('verified_summary','summarize_round02_english.py','--candidate',CANDIDATE)\n    py('resource_receipts','report_bounded_execution.py')")
    ast.parse(source);out.write_text(source,encoding='utf8')
print('Prepared train09 trainer, training preflight and bounded pipeline; no execution.')
