import json,hashlib
from pathlib import Path
from run_suite import run_case,write
W=Path(__file__).resolve().parents[1]
selected=json.loads((W/'protocol/selected_final.json').read_text());add=json.loads((W/'protocol/completion_addendum.json').read_text())
source=add['known_failure_retest'];case={k:source[k] for k in ['scene','color','kind','model']};case['id']=source['case_id']
suite=W/'runs'/('known_failure_'+selected['candidate']);suite.mkdir(parents=True,exist_ok=False)
ck=W/'models'/selected['candidate']/'final'
assert hashlib.sha256((ck/'model.safetensors').read_bytes()).hexdigest()==selected['checkpoint_sha256']
assert hashlib.sha256((W.parent/'validation_v1_1/scenes/swapped/physics/rescue_scene.xml').read_bytes()).hexdigest()==source['physics_sha256']
write(suite/'suite_plan.json',dict(cases=[case],checkpoint_sha256=selected['checkpoint_sha256'],addendum_sha256=hashlib.sha256((W/'protocol/completion_addendum.json').read_bytes()).hexdigest(),automatic_retries=0))
result=run_case(case,ck,suite/(case['id']+'_'+case['model']))
write(suite/'summary.json',dict(completed=1,planned=1,successes=int(result['success']),cases=[result]))
