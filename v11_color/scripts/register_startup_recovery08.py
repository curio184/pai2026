"""Preserve an empty, pre-flight failed attempt and register one explicit recovery."""
import ast,datetime,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
status=W/'pipeline_train08_en_status.json';assert read(status)['stage']=='pipeline_error'
source=W/'runs/dev_train08_en/dev01_blue_v1.1'
dest=source.with_name('dev01_blue_v1.1_startup_failed01')
assert source.is_dir() and not list(source.iterdir()) and not dest.exists()
assert source.resolve().is_relative_to((W/'runs').resolve()) and dest.resolve().is_relative_to((W/'runs').resolve())
log=W/'logs/pipeline08_en_dev.log';message=log.read_text()
assert 'OSError: [Errno 22]' in message and 'arducopter' in message
assert 'case_start' not in message
resume=W/'scripts/resume_train08_after_startup.py';ast.parse(resume.read_text())
original=(W/'scripts/pipeline_train08_en.py').read_text()
def workflow(text):
    main=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    index=next(i for i,n in enumerate(main.body) if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and any(isinstance(v,ast.Name) and v.id=='suite' for v in n.target.elts))
    return [ast.dump(n) for n in main.body[index:]]
# The workflow is copied exactly except cosmetic line wrapping of final status.
assert workflow(original)==workflow(resume.read_text())
plan=read(W/'runs/dev_train08_en/suite_plan.json')
record=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    kind='infrastructure failure before flight',flight_started=False,inference_started=False,
    case=plan['cases'][0],original_empty_directory=str(source.relative_to(W)),
    preserved_directory=str(dest.relative_to(W)),original_directory_created=source.stat().st_ctime,
    original_log_sha256=sha(log),original_status=read(status),
    checkpoint_sha256=read(W/'models/train08_en/result.json')['checkpoint_sha256'],
    resume_script_sha256=sha(resume),unchanged_suite_plan_sha256=sha(W/'runs/dev_train08_en/suite_plan.json'),
    runtime_lock_sha256=sha(W/'protocol/runtime_english_lock.json'),
    resolution='WSL read-only wake/check succeeded; original ArduPilot SHA unchanged. No restart or file-content repair.',
    scope='One explicit recovery. No flight/inference occurred in the failed startup. No score, model, runtime, criteria or planned case changes. Not counted as a flight success or flight failure; listed separately.')
out=W/'protocol/train08_startup_recovery01.json';assert not out.exists()
out.write_text(json.dumps(record,indent=2),encoding='utf8')
source.rename(dest)
shutil.copy2(log,dest/'startup_error.log');shutil.copy2(status,dest/'pipeline_error.json')
(dest/'startup_failure.json').write_text(json.dumps(record,indent=2),encoding='utf8')
assert sha(dest/'startup_error.log')==record['original_log_sha256']
print(json.dumps(dict(registered=True,flight_started=False,preserved=str(dest),plan_sha256=sha(out))))
