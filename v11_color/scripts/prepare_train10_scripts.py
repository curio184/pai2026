"""Prepare new filenames only; do not train, infer, fly, or mutate frozen scripts."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
for name in ['train09_en.py','preflight_train09_loss.py','pipeline_train09_en.py','freeze_train09_implementation.py','monitor_train09.py']:
    new=name.replace('train09','train10');out=W/'scripts'/new;assert not out.exists()
    source=(W/'scripts'/name).read_text(encoding='utf8')
    source=source.replace('train09','train10').replace('Train09','Train10').replace('dataset09','dataset10').replace('teacher_flight09','teacher_flight10').replace('pipeline09_en_','pipeline10_en_')
    if name=='train09_en.py':
        source=source.replace("W/'scripts/teacher_flight10.py',W/'scripts/teacher_flight08.py'", "W/'scripts/teacher_flight10.py',W/'scripts/teacher_flight09.py',W/'scripts/teacher_flight08.py'")
        source=source.replace('All pixels and existing nonhorizontal labels preserved. Stationary horizontal teacher relabeled to mild -0.6 captured-velocity braking; grounded takeoff zero. Navigation and all nonhorizontal labels preserved; no new inputs.',
            'All pixels and inputs preserved. Only armed airborne rotation yaw labels use a tighter 0.03rad deadband; yaw loss weight 4. All non-yaw labels and navigation/landing labels are byte-identical to train09. No runtime changes.')
    if name=='freeze_train09_implementation.py':
        source=source.replace("'teacher_flight10.py','teacher_flight08.py'", "'teacher_flight10.py','teacher_flight09.py','teacher_flight08.py'")
    ast.parse(source);out.write_text(source,encoding='utf8')
print('Prepared train10 trainer, preflight, bounded pipeline, lock generator and monitor.')
