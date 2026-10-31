"""Create isolated candidate16 files; previous attempts remain byte-identical."""
import ast
from pathlib import Path
S=Path(__file__).resolve().parent
def make(source,dest,changes):
    p=S/dest
    assert not p.exists()
    text=(S/source).read_text(encoding='utf8')
    for old,new in changes:
        assert old in text,(source,old)
        text=text.replace(old,new)
    ast.parse(text)
    p.write_text(text,encoding='utf8')

make('train15_en.py','train16_en.py',[
    ('Train15 English: fixed 6,000','Train16 English: fixed 6,000'),
    ('train15','train16'),('dataset15','dataset16'),
    ("W/'scripts/teacher_flight15.py'","W/'scripts/teacher_flight16.py',W/'scripts/teacher_flight15.py'"),
    ('Same audited dataset14 inputs and sampling. All navigation targets unchanged; stationary braking0.6.',
     'Same audited dataset15 inputs and sampling. All navigation targets unchanged; stationary targets use0.6*velocity-0.9*9.81*tan(pitch,roll).')])
make('pipeline_train15_en.py','pipeline_train16_en.py',[('train15','train16'),('pipeline15','pipeline16')])
make('preflight_train15_loss.py','preflight_train16_loss.py',[('train15','train16'),('dataset15','dataset16')])
make('freeze_train15_implementation.py','freeze_train16_implementation.py',[
    ('train15','train16'),('dataset15','dataset16'),
    ("'teacher_flight15.py'","'teacher_flight16.py','teacher_flight15.py'")])
make('monitor_train15.py','monitor_train16.py',[('train15','train16')])
make('verify_train15_final_checkpoint.py','verify_train16_final_checkpoint.py',[('train15','train16')])
print('Created isolated candidate16 trainer/pipeline/audits/monitor. No training executed.')
