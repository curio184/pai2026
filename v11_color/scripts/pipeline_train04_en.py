"""English-only training and preregistered development/final evaluation gates."""
import datetime,json,subprocess,sys
from pathlib import Path
from run_round02_english import stress_pass
from run_suite_english import lock_check,sha
W=Path(__file__).resolve().parents[1]
PLOT='C:/Temp/pai2026_submission/check_env/Scripts/python.exe'
BLENDER='C:/Program Files/Blender Foundation/Blender 3.1/blender.exe'
CANDIDATE='train04_en'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def status(stage,**kwargs):
    obj=dict(stage=stage,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kwargs)
    (W/'pipeline_train04_en_status.json').write_text(json.dumps(obj,indent=2),encoding='utf-8');print(json.dumps(obj),flush=True)
def run(stage,command):
    implementation=read(W/'protocol/train04_english_implementation.json')
    for name,h in implementation['scripts'].items():assert sha(W/'scripts'/name)==h,name
    status(stage,state='running')
    with (W/'logs'/('pipeline04_en_'+stage+'.log')).open('x',encoding='utf-8') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError(f'{stage} returned {result.returncode}; attempt preserved')
def py(stage,script,*args):run(stage,[sys.executable,str(W/'scripts'/script),*args])
def main():
    assert not (W/'models'/CANDIDATE).exists()
    lock_check()
    transition=next(r for r in read(W/'probe_english_transition/outputs/summary.json')['summary'] if r['model']=='v1.1')
    assert transition['prompt_group']=='runtime_english' and transition['correct_goal']>=60 and transition['whole_quartet_correct']>=14
    implementation=read(W/'protocol/train04_english_implementation.json')
    for name,h in implementation['scripts'].items():assert sha(W/'scripts'/name)==h,name
    for layout in read(W/'protocol/round02_english.json')['heldout_layouts']:
        provenance=read(W/'scenes'/layout['name']/'provenance.json')
        assert provenance['plan_sha256']==sha(W/'protocol/round02_english.json') and provenance['layout']==layout
    py('training','train04_en.py')
    for suite,expected in [('dev',8),('stress',16),('regression',5),('known_failure',1)]:
        py(suite,'run_round02_english.py',suite,'--candidate',CANDIDATE)
        summary=read(W/'runs'/(suite+'_'+CANDIDATE)/'summary.json')
        assert summary['completed']==summary['planned']==expected
        passed=stress_pass(summary) if suite=='stress' else summary['successes']==expected
        if not passed:
            status('development_review',failed_suite=suite,successes=summary['successes'],planned=expected,fresh_final_evaluation_not_started=True,automatic_retraining=False);return
    py('select','run_round02_english.py','select','--candidate',CANDIDATE)
    py('heldout','run_round02_english.py','heldout','--candidate',CANDIDATE)
    run('render_probe',[BLENDER,'--factory-startup','--background','--python',str(W/'scripts/render_probe_round02_english.py')])
    py('probe_inference','run_probe_round02_english.py')
    run('probe_figures',[PLOT,str(W/'scripts/plot_probe_round02_english.py')])
    py('round_summary','round_summary.py','--suite','heldout_round02_english_'+CANDIDATE,'--protocol','protocol/round02_english.json')
    py('trial_index','trial_index.py')
    py('rescore','verify_records.py','--output',str(W/'reports/all_records_round02_english_verified.json'))
    flight=read(W/'reports'/('heldout_round02_english_'+CANDIDATE+'_round_summary.json'))
    probe=next(r for r in read(W/'probe_round02_english/outputs/summary.json')['summary'] if r['model']=='v1.1')
    status('evidence_ready',flight_gate_met=flight['flight_round_gate_met'],color_gate_met=probe['correct_goal']>=60 and probe['whole_quartet_correct']>=14,
        documents_and_final_audit_pending=True,automatic_retraining=False,published=False)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        status('pipeline_error',error=repr(exc));raise
