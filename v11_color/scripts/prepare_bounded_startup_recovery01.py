"""Preserve a proven preflight WSL connection failure; no trial or model selection."""
import ast,datetime,hashlib,json,subprocess
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf8')

suite=W/'runs/dev_train08_en_capped';failed=suite/'primitive_red_v1.1'
saved=suite/'primitive_red_v1.1_startup_failed01'
assert failed.exists() and not saved.exists()
outcome=read(failed/'outcome.json')
assert outcome['runner_exit']==4294967295 and not outcome['success']
assert not (failed/'record').exists() and not (failed/'resource_limits.json').exists()
assert not (failed/'resource_usage.json').exists()
log=(failed/'runner.log').read_bytes().decode('utf-16-le')
assert 'Wsl/Service/WSAETIMEDOUT' in log
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*'))
summary=read(suite/'summary.json');assert summary['completed']==6 and summary['successes']==5
assert all(r['success'] for r in summary['cases'][:5])
assert summary['cases'][-1]['id']=='primitive_red'
from run_suite_english import lock_check
lock_check()
subprocess.run(['wsl','-d','Ubuntu-22.04','--exec','/bin/true'],check=True,timeout=15)

original=W/'scripts/pipeline_train08_capped.py';target=W/'scripts/resume_train08_capped_startup01.py'
assert not target.exists()
source=original.read_text(encoding='utf8')
source=source.replace('Explicitly reviewed recovery from a pre-flight WSL path-read failure.',
    'Resume remaining bounded cases after a preserved preflight WSL connection failure.')
source=source.replace("pipeline_train08_capped_status.json","pipeline_train08_capped_recovery01_status.json")
source=source.replace("pipeline08_capped_","pipeline08_capped_recovery01_")
source=source.replace("assert limits['scripts'][Path(__file__).name]==sha(Path(__file__))",
    "recovery=read(W/'protocol/bounded_startup_recovery01.json')\n    assert recovery['recovery_script_sha256']==sha(Path(__file__))\n    assert limits['scripts']['pipeline_train08_capped.py']==sha(W/'scripts/pipeline_train08_capped.py')")
ast.parse(source);target.write_text(source,encoding='utf8')
manifest={p.relative_to(failed).as_posix():sha(p) for p in failed.rglob('*') if p.is_file()}
plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    reason='WSL service connection timeout before bounded wrapper/simulator started; WSL responded again without restarting it.',
    original_folder=failed.relative_to(W).as_posix(),preserved_folder=saved.relative_to(W).as_posix(),
    original_files_sha256=manifest,original_summary=summary,original_summary_sha256=sha(suite/'summary.json'),
    original_outcome_flight_started=True,
    correction='flight_started in the launcher means subprocess launch was requested. No resource_limits.json or record directory was created; the Linux wrapper and flight did not start.',
    flight_started=False,model_inference_started=False,normal_performance_trial=False,
    recovery_script=target.name,recovery_script_sha256=sha(target),
    original_pipeline_sha256=sha(original),resource_protocol_sha256=sha(W/'protocol/bounded_execution.json'),
    candidate='train08_en_capped',checkpoint_sha256=read(W/'models/train08_en/result.json')['checkpoint_sha256'],
    conditions_changed=False,model_changed=False,criteria_changed=False,
    continuation='Reuse the five completed outcomes without rerunning them; execute the three remaining predefined cases once. Preserve any further infrastructure error and stop for diagnosis.',
    windows_worker_and_renderer_cleaned_by_runner=True,global_wsl_restart=False)
registration=W/'protocol/bounded_startup_recovery01.json';assert not registration.exists()
write(registration,plan)
assert failed.resolve().is_relative_to((W/'runs').resolve()) and saved.resolve().is_relative_to((W/'runs').resolve())
failed.rename(saved)
assert all(sha(saved/name)==h for name,h in manifest.items())
write(saved/'startup_failure.json',plan)
print(json.dumps(dict(registered=True,registration_sha256=sha(registration),preserved_files=len(manifest),flight_started=False,remaining_cases=3)))
