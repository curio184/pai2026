"""Freeze execution resource limits before any new bounded flight."""
import datetime,hashlib,json
from pathlib import Path
from run_suite_english import lock_check
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock_check()
assert not (W/'runs/dev_train08_en_capped').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert read(W/'reports/wsl_bounded_smoke/result.json')['exit']==0
source=W/'models/train08_en/final/model.safetensors';alias=W/'models/train08_en_capped/final/model.safetensors'
assert sha(source)==sha(alias)==read(W/'models/train08_en/result.json')['checkpoint_sha256']
files=['bounded_wsl.py','bounded_wsl_entry.py','run_suite_bounded.py','run_round02_bounded.py','pipeline_train08_capped.py']
plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    requested_by_user='WSL may be used, but avoid load; up to 4 CPUs and 8GB.',
    evaluation_alias='train08_en_capped',source_candidate='train08_en',new_training=False,
    checkpoint_sha256=sha(source),cpu_quota_cores=4,allowed_cpus=[0,1,2,3],memory_max_bytes=8*1024**3,memory_high_bytes=6*1024**3,nice=10,max_concurrent_flights=1,
    scope='Only each project simulation process tree. Global WSL settings and other workloads unchanged.',
    scripts={n:sha(W/'scripts'/n) for n in files},diff_sha256=sha(W/'protocol/bounded_execution.diff'),
    original_runtime_lock_sha256=sha(W/'protocol/runtime_lock.json'),english_runtime_lock_sha256=sha(W/'protocol/runtime_english_lock.json'),
    round_protocol_sha256=sha(W/'protocol/round02_english.json'),probe_protocol_sha256=sha(W/'protocol/static_probe_round02_english.json'),
    preservation='Original startup failure and user-interrupted flight retained under runs/dev_train08_en; no retry overwrites.',
    interpretation='Resource scheduling can affect wall-clock timing. Both v1.0 and v1.1 final comparison flights use these same limits; do not pool earlier execution conditions.',
    success_criteria_changed=False,controller_model_gains_changed=False,
    test_conditions='Original cases, layouts, seeds, repetitions and criteria unchanged. Only process resource limits and process priority change.',
    smoke_report_sha256=sha(W/'reports/wsl_bounded_smoke/resource_usage.json'))
out=W/'protocol/bounded_execution.json';assert not out.exists();out.write_text(json.dumps(plan,indent=2),encoding='utf8')
print(json.dumps(dict(registered=True,plan_sha256=sha(out),checkpoint_sha256=plan['checkpoint_sha256'],new_training=False)))
