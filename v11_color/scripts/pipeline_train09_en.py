"""English-only training and preregistered development/final evaluation gates."""
import os
os.environ["PYTHONUTF8"]="1"
import datetime,json,subprocess,sys
from pathlib import Path
from run_round02_english import stress_pass
from run_suite_english import lock_check,sha
W=Path(__file__).resolve().parents[1]
PLOT='C:/Temp/pai2026_submission/check_env/Scripts/python.exe'
BLENDER='C:/Program Files/Blender Foundation/Blender 3.1/blender.exe'
CANDIDATE='train09_en'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def status(stage,**kwargs):
    obj=dict(stage=stage,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kwargs)
    (W/'pipeline_train09_en_status.json').write_text(json.dumps(obj,indent=2),encoding='utf-8');print(json.dumps(obj),flush=True)
def run(stage,command):
    implementation=read(W/'protocol/train09_english_implementation.json')
    for name,h in implementation['scripts'].items():assert sha(W/'scripts'/name)==h,name
    status(stage,state='running',resources='4 CPUs / 8GiB / nice 10 / one flight at a time')
    with (W/'logs'/('pipeline09_en_'+stage+'.log')).open('x',encoding='utf-8') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError(f'{stage} returned {result.returncode}; attempt preserved')
def py(stage,script,*args):run(stage,[sys.executable,'-X','utf8',str(W/'scripts'/script),*args])
def collect_evidence():
    py('all_trial_summary','summarize_round02_english.py','--candidate',CANDIDATE)
    py('all_trial_index','trial_index_round02_english.py')
    py('all_trial_rescore','verify_records_round02_english.py','--output',str(W/'reports'/(CANDIDATE+'_all_records_verified.json')))
    py('verified_summary','summarize_round02_english.py','--candidate',CANDIDATE)
    py('resource_receipts','report_bounded_execution.py')

def main():
    assert not (W/'models'/CANDIDATE).exists()
    lock_check()
    assert read(W/'reports/train09_loss_preflight_audit.json')['passed']
    transition=next(r for r in read(W/'probe_english_transition/outputs/summary.json')['summary'] if r['model']=='v1.1')
    assert transition['prompt_group']=='runtime_english' and transition['correct_goal']>=60 and transition['whole_quartet_correct']>=14
    implementation=read(W/'protocol/train09_english_implementation.json')
    for name,h in implementation['scripts'].items():assert sha(W/'scripts'/name)==h,name
    for layout in read(W/'protocol/round02_english.json')['heldout_layouts']:
        provenance=read(W/'scenes'/layout['name']/'provenance.json')
        assert provenance['plan_sha256']==sha(W/'protocol/round02_english.json') and provenance['layout']==layout
    py('training','train09_en.py')
    py('saved_weights_audit','verify_saved_training.py','--candidate',CANDIDATE)
    for suite,expected in [('dev',8),('stress',16),('regression',5),('known_failure',1)]:
        py(suite,'run_round02_bounded.py',suite,'--candidate',CANDIDATE)
        summary=read(W/'runs'/(suite+'_'+CANDIDATE)/'summary.json')
        assert summary['completed']==summary['planned']==expected
        passed=stress_pass(summary) if suite=='stress' else summary['successes']==expected
        py(suite+'_rescore','verify_suite_records.py','--suite',suite+'_'+CANDIDATE)
        py(suite+'_phase_diagnostic','phase_diagnostics.py','--suite',suite+'_'+CANDIDATE)
        py(suite+'_failures','failure_details.py','--suite',suite+'_'+CANDIDATE)
        if not passed:
            collect_evidence()
            status('development_review',failed_suite=suite,successes=summary['successes'],planned=expected,fresh_final_evaluation_not_started=True,automatic_retraining=False);return
    py('select','run_round02_bounded.py','select','--candidate',CANDIDATE)
    py('heldout','run_round02_bounded.py','heldout','--candidate',CANDIDATE)
    run('render_probe',[BLENDER,'--factory-startup','--background','--python',str(W/'scripts/render_probe_round02_english.py')])
    py('probe_inference','run_probe_round02_english.py')
    run('probe_figures',[PLOT,'-X','utf8',str(W/'scripts/plot_probe_round02_english.py')])
    py('round_summary','round_summary.py','--suite','heldout_round02_english_'+CANDIDATE,'--protocol','protocol/round02_english.json')
    collect_evidence()
    flight=read(W/'reports'/('heldout_round02_english_'+CANDIDATE+'_round_summary.json'))
    probe=next(r for r in read(W/'probe_round02_english/outputs/summary.json')['summary'] if r['model']=='v1.1')
    status('evidence_ready',flight_gate_met=flight['flight_round_gate_met'],color_gate_met=probe['correct_goal']>=60 and probe['whole_quartet_correct']>=14,
        documents_and_final_audit_pending=True,automatic_retraining=False,published=False)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        status('pipeline_error',error=repr(exc));raise
