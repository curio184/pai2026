"""Prepare a separate resumed pipeline, preserving the original error/status."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
s=(W/'scripts/pipeline_train13_en.py').read_text(encoding='utf8')
s=s.replace('pipeline_train13_en_status.json','pipeline_train13_resume01_status.json').replace('pipeline13_en_','pipeline13_resume01_')
s=s.replace("assert not (W/'models'/CANDIDATE).exists()", "assert (W/'models'/CANDIDATE).exists() and not (W/'models'/CANDIDATE/'final').exists()\n    amendment=read(W/'protocol/train13_resume01.json')\n    assert sha(Path(__file__))==amendment['resume_pipeline_sha256']\n    assert sha(W/'scripts/train13_resume01.py')==amendment['resume_trainer_sha256']\n    assert sha(W/'protocol/train13_english.json')==amendment['original_plan_sha256']\n    assert not (W/'runs/dev_train13_en').exists()\n    assert not (W/'protocol/selected_final_round02_english.json').exists()")
s=s.replace("py('training','train13_en.py')", "py('training_resume01','train13_resume01.py')")
out=W/'scripts/pipeline_train13_resume01.py';assert not out.exists();ast.parse(s);out.write_text(s,encoding='utf8')
m=(W/'scripts/monitor_train13.py').read_text(encoding='utf8').replace('pipeline_train13_en.py','pipeline_train13_resume01.py').replace('pipeline_train13_en_status.json','pipeline_train13_resume01_status.json')
m=m.replace("['progress','result','failure']", "['progress','result','failure_resume01']")
out=W/'scripts/monitor_train13_resume01.py';assert not out.exists();ast.parse(m);out.write_text(m,encoding='utf8')
print('Prepared resumed pipeline and monitor; no training started.')
