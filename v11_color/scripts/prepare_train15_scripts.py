"""Create isolated candidate15 files; do not modify previous attempts."""
import ast
from pathlib import Path
S=Path(__file__).resolve().parent
def make(source,dest,changes):
    p=S/dest;assert not p.exists();text=(S/source).read_text(encoding='utf8')
    for old,new in changes:
        assert old in text,(source,old);text=text.replace(old,new)
    ast.parse(text);p.write_text(text,encoding='utf8')
make('train14_en.py','train15_en.py',[
    ('Train14 English: fixed 8,000','Train15 English: fixed 6,000'),
    ('train14','train15'),('dataset14','dataset15'),
    ("W/'scripts/teacher_flight14.py'","W/'scripts/teacher_flight15.py',W/'scripts/teacher_flight14.py'"),
    ("{'runtime_fixed':32000,'random':32000}","{'runtime_fixed':24000,'random':24000}"),
    ('Same audited dataset13 inputs and sampling. Navigation yaw anticipates1s of own linear/angular motion; stationary braking1.6.',
     'Same audited dataset14 inputs and sampling. All navigation targets unchanged; stationary braking0.6.')])
make('pipeline_train14_en.py','pipeline_train15_en.py',[('train14','train15'),('pipeline14','pipeline15')])
make('preflight_train14_loss.py','preflight_train15_loss.py',[('train14','train15'),('dataset14','dataset15')])
make('freeze_train14_implementation.py','freeze_train15_implementation.py',[
    ('train14','train15'),('dataset14','dataset15'),
    ("'teacher_flight14.py'","'teacher_flight15.py','teacher_flight14.py'")])
make('monitor_train14.py','monitor_train15.py',[('train14','train15')])
make('verify_train14_final_checkpoint.py','verify_train15_final_checkpoint.py',[
    ('train14','train15'),('8000','6000'),('8001','6001'),('32000','24000'),('64000','48000')])
print('Created isolated candidate15 trainer/pipeline/audits/monitor. Nothing executed.')
