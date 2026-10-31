"""Prepare a new, separately recorded attempt without changing older attempts."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
for name in ['train12_en.py','preflight_train12_loss.py','pipeline_train12_en.py','freeze_train12_implementation.py','monitor_train12.py','diagnose_train12_postflight.py']:
    out=W/'scripts'/name.replace('train12','train13'); assert not out.exists()
    s=(W/'scripts'/name).read_text(encoding='utf8').replace('train12','train13').replace('Train12','Train13').replace('pipeline12_en_','pipeline13_en_').replace('dataset12_en','dataset13_en')
    if name=='train12_en.py':
        s=s.replace("W/'scripts/teacher_flight13.py',W/'scripts/teacher_flight10.py',", "W/'scripts/teacher_flight13.py',W/'scripts/teacher_flight12.py',W/'scripts/teacher_flight10.py',")
        s=s.replace('Same dataset10 inputs and sampling; stronger stationary braking and latency-aware rotation targets under train13 plan. Half fixed runtime noise and half random noise retained. Navigation/landing labels and runtime unchanged; no evaluation inputs in training.', 'Same audited dataset12 inputs and sampling. Navigation teacher additionally centers the requested person with yaw; body velocity is rolled out consistently as heading changes. Primitive and landing labels unchanged. Half fixed runtime noise and half random noise retained. Runtime unchanged; no evaluation inputs in training.')
    if name=='pipeline_train12_en.py':
        s=s.replace("assert read(W/'reports/train13_loss_preflight_audit.json')['passed']", "assert read(W/'reports/train13_loss_preflight_audit.json')['passed']\n    assert read(W/'reports/train13_teacher_preflight_audit.json')['passed']")
    if name=='freeze_train12_implementation.py':
        s=s.replace("'teacher_flight13.py','teacher_flight10.py',", "'teacher_flight13.py','teacher_flight12.py','teacher_flight10.py',")
        s=s.replace("'preflight_train13_loss.py',", "'preflight_train13_loss.py','preflight_train13_teacher.py',")
    if name=='diagnose_train12_postflight.py':
        s=s.replace("assert manifest['yaw_cap_rad_s']==.25 and manifest['yaw_capture_lookahead_s']==1.0", "assert manifest['yaw_cap_rad_s']==.25 and manifest['yaw_capture_lookahead_s']==1.0\n    assert manifest['navigation_yaw_cap_rad_s']==.25 and manifest['navigation_yaw_deadband_rad']==.05")
    ast.parse(s); out.write_text(s,encoding='utf8')
print('Prepared train13 scripts only; no registration, optimization, or inference performed.')
