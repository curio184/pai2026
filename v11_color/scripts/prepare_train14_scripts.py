"""Create isolated candidate14 scripts without modifying any prior attempt."""
import ast
from pathlib import Path
S=Path(__file__).resolve().parent
def transform(source,dest,changes):
    p=S/dest;assert not p.exists();text=(S/source).read_text(encoding='utf8')
    for old,new in changes:
        assert old in text,(source,old);text=text.replace(old,new)
    ast.parse(text);p.write_text(text,encoding='utf8')
transform('train13_en.py','train14_en.py',[
    ('Train13 English: fixed 6,000','Train14 English: fixed 8,000'),
    ('train13','train14'),('dataset13','dataset14'),
    ("W/'scripts/teacher_flight12.py'","W/'scripts/teacher_flight14.py',W/'scripts/teacher_flight13.py',W/'scripts/teacher_flight12.py'"),
    ('if step%1000==0:',"if step%plan['recovery_interval_steps']==0:"),
    ("temp=out/'recovery.pt.tmp';torch.save(snap,temp);temp.replace(out/'recovery.pt');del snap",
     "save=out/f'recovery_step{step:05d}.pt';assert not save.exists()\n                snap.update(noise_exposure=noise_exposure,batch_type_counts=batch_types,elapsed_s=time.monotonic()-start,plan_sha256=sha(planfile))\n                with save.open('xb') as stream:torch.save(snap,stream)\n                write(save.with_suffix('.json'),dict(step=step,bytes=save.stat().st_size,sha256=sha(save),plan_sha256=sha(planfile)))\n                del snap"),
    ("{'runtime_fixed':24000,'random':24000}","{'runtime_fixed':32000,'random':32000}"),
    ('Same audited dataset12 inputs and sampling. Navigation teacher additionally centers the requested person with yaw; body velocity is rolled out consistently as heading changes. Primitive and landing labels unchanged.',
     'Same audited dataset13 inputs and sampling. Navigation yaw anticipates1s of own linear/angular motion; stationary braking1.6. Vertical/request targets, primitive yaw and landing labels unchanged.')])
transform('pipeline_train13_en.py','pipeline_train14_en.py',[('train13','train14'),('pipeline13','pipeline14')])
transform('preflight_train13_loss.py','preflight_train14_loss.py',[('train13','train14'),('dataset13','dataset14')])
transform('freeze_train13_implementation.py','freeze_train14_implementation.py',[
    ('train13','train14'),('dataset13','dataset14'),
    ("'teacher_flight12.py'","'teacher_flight14.py','teacher_flight13.py','teacher_flight12.py'")])
transform('monitor_train13.py','monitor_train14.py',[('train13','train14')])
print('Candidate14 isolated trainer, pipeline, preflight, implementation lock and monitor created; no execution yet.')
