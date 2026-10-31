"""Preserve interruption evidence and prepare a distinct execution alias, not a new model."""
import ast,datetime,difflib,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf8')
folder=W/'runs/dev_train08_en/dev01_blue_v1.1'
case=read(folder.parent/'suite_plan.json')['cases'][0]
score=read(folder/'record/search_score.json');assert not score['success']
assert (W/'reports/user_stop_wsl_completed.json').exists()
outcome=dict(id=case['id'],model=case['model'],case=case,flight_started=True,
    success=score['success'],record=str(folder/'record'),checkpoint_sha256=read(folder/'manifest.json')['checkpoint_sha256'],
    checks=score['checks'],error='Interrupted by explicit user request to stop WSL; subsequent permission requires bounded resources.',
    user_interrupted=True,normal_performance_trial=False,runner_exit_not_collected=True,
    interruption_receipt_sha256=sha(W/'reports/user_stop_wsl_completed.json'))
assert not (folder/'outcome.json').exists();write(folder/'outcome.json',outcome)
write(folder.parent/'summary.json',dict(completed=1,planned=8,successes=0,cases=[outcome],user_interrupted=True))
source=W/'models/train08_en';alias=W/'models/train08_en_capped';alias.mkdir(exist_ok=False)
for name in ['started.json','result.json','sampling_exposure.json','frozen_backbone_verification.json']:
    shutil.copy2(source/name,alias/name);assert sha(source/name)==sha(alias/name)
write(alias/'evaluation_alias.json',dict(source_candidate='train08_en',reason='Same final weights; execution limited to four CPUs and 8GiB after user request.',new_training=False,checkpoint_sha256=read(source/'result.json')['checkpoint_sha256']))
text=(W/'scripts/resume_train08_after_startup.py').read_text()
text=text.replace('CANDIDATE=base.CANDIDATE','CANDIDATE="train08_en_capped"')
text=text.replace('read=base.read;status=base.status;py=base.py;collect_evidence=base.collect_evidence',
'''read=base.read;py=base.py;collect_evidence=base.collect_evidence
base.CANDIDATE=CANDIDATE
def status(stage,**kwargs):
    import datetime
    obj=dict(stage=stage,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kwargs)
    (W/'pipeline_train08_capped_status.json').write_text(json.dumps(obj,indent=2),encoding='utf8');print(json.dumps(obj),flush=True)
base.status=status''')
text=text.replace("    implementation=read(W/'protocol/train08_english_implementation.json')", "    limits=read(W/'protocol/bounded_execution.json')\n    for name,h in limits['scripts'].items():assert sha(W/'scripts'/name)==h,name\n    implementation=read(W/'protocol/train08_english_implementation.json')")
text=text.replace("recovery='startup01; no prior flight was started'", "resources='4 CPUs, 8GiB, nice 10; one flight at a time'")
text=text.replace('pipeline08_recovery01_','pipeline08_capped_')
start=text.index("    recovery=read(W/'protocol/train08_startup_recovery01.json')")
end=text.index("    subprocess.run(['wsl'",start)
text=text[:start]+'''    limits=read(W/'protocol/bounded_execution.json')
    assert limits['scripts'][Path(__file__).name]==sha(Path(__file__))
    assert sha(W/'models'/CANDIDATE/'final/model.safetensors')==limits['checkpoint_sha256']
    assert read(W/'reports/train08_en_saved_training_verification.json')['passed']
    assert read(W/'models'/CANDIDATE/'result.json')['optimizer_steps_completed']==4000
    assert not (W/'protocol/selected_final_round02_english.json').exists()
'''+text[end:]
text=text.replace("'run_round02_english.py'","'run_round02_bounded.py'").replace("recovery='startup01'","resources='bounded execution'")
dest=W/'scripts/pipeline_train08_capped.py';assert not dest.exists();ast.parse(text);dest.write_text(text,encoding='utf8')
diff=[]
for a,b in [('run_suite_english.py','run_suite_bounded.py'),('run_round02_english.py','run_round02_bounded.py')]:
    diff.extend(difflib.unified_diff((W/'scripts'/a).read_text().splitlines(True),(W/'scripts'/b).read_text().splitlines(True),fromfile=a,tofile=b))
(W/'protocol/bounded_execution.diff').write_text(''.join(diff),encoding='utf8')
print('Interruption preserved; evaluation alias metadata and bounded pipeline prepared. No flight started.')
