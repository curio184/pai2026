"""Preserve and disclose an offline teacher-reference correction."""
import datetime, hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
original=W/'reports/dev_train13_en_postflight_development_diagnostic.json'
corrected=W/'reports/dev_train13_en_postflight_development_diagnostic_v2.json'
a=json.loads(original.read_text()); b=json.loads(corrected.read_text())
assert a['teacher_source_sha256']==sha(W/'scripts/teacher_flight12.py')
assert b['teacher_source_sha256']==sha(W/'scripts/teacher_flight13.py')
for x,y in zip(a['cases'],b['cases'],strict=True):
    for key in ['id','success','failure','stop_reason','goal_hold_s','initial_hover_s','events_sha256','trace_sha256']:
        assert x[key]==y[key],key
out=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    original_report=str(original), original_sha256=sha(original),
    corrected_report=str(corrected), corrected_sha256=sha(corrected),
    issue='The first train13 offline diagnosis imported teacher_flight12, omitting train13 navigation yaw targets.',
    resolution='Separate v2 diagnostic uses teacher_flight13. The original report and script are preserved. All train13 teacher-error interpretations must use v2.',
    trial_outcomes_and_raw_records_unchanged=True,
    no_training_or_runtime_change=True,
    stress_diagnostic='Use diagnose_train13_postflight_v2.py after the full stress suite completes.')
dest=W/'reports/train13_diagnostic_reference_correction.json'
assert not dest.exists()
dest.write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(out))
