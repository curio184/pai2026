"""New attempt scripts; preserve all earlier training and runtime files."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
for name in ['train11_en.py','preflight_train11_loss.py','pipeline_train11_en.py','freeze_train11_implementation.py','monitor_train11.py']:
    out=W/'scripts'/name.replace('train11','train12');assert not out.exists()
    s=(W/'scripts'/name).read_text(encoding='utf8').replace('train11','train12').replace('Train11','Train12').replace('pipeline11_en_','pipeline12_en_').replace('dataset10_en','dataset12_en')
    if name=='train11_en.py':
        s=s.replace("W/'scripts/teacher_flight10.py',", "W/'scripts/teacher_flight12.py',W/'scripts/teacher_flight10.py',")
        s=s.replace('Same audited dataset10 images, states, labels, sampler, loss weights and flow-time schedule. Half of training microbatches use the already frozen runtime Gaussian noise realization, half fresh random noise. No runtime changes or evaluation inputs in training.', 'Same dataset10 inputs and sampling; stronger stationary braking and latency-aware rotation targets under train12 plan. Half fixed runtime noise and half random noise retained. Navigation/landing labels and runtime unchanged; no evaluation inputs in training.')
    if name=='freeze_train11_implementation.py':
        s=s.replace("assert sha(audit)==read(plan)['training']['source_dataset_audit_sha256']\nassert read(audit)['plan_sha256']==sha(W/'protocol/train10_english.json')", "assert read(audit)['plan_sha256']==sha(plan)")
        s=s.replace("'teacher_flight10.py',", "'teacher_flight12.py','teacher_flight10.py',")
    ast.parse(s);out.write_text(s,encoding='utf8')
print('Prepared train12; bounded runtime and acceptance gates unchanged.')
