"""Explicitly reviewed recovery from a pre-flight WSL path-read failure."""
import json,subprocess,sys
from pathlib import Path
import pipeline_train08_en as base
from run_round02_english import stress_pass
from run_suite_english import lock_check,sha
W=base.W;CANDIDATE=base.CANDIDATE;PLOT=base.PLOT;BLENDER=base.BLENDER
read=base.read;status=base.status;py=base.py;collect_evidence=base.collect_evidence

def run(stage,command):
    implementation=read(W/'protocol/train08_english_implementation.json')
    for name,h in implementation['scripts'].items():assert sha(W/'scripts'/name)==h,name
    status(stage,state='running',recovery='startup01; no prior flight was started')
    with (W/'logs'/('pipeline08_recovery01_'+stage+'.log')).open('x',encoding='utf8') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError(f'{stage} returned {result.returncode}; attempt preserved')

base.run=run

def main():
    recovery=read(W/'protocol/train08_startup_recovery01.json')
    assert recovery['resume_script_sha256']==sha(Path(__file__))
    assert recovery['flight_started'] is False and recovery['inference_started'] is False
    assert sha(W/'models/train08_en/final/model.safetensors')==recovery['checkpoint_sha256']
    assert read(W/'reports/train08_en_saved_training_verification.json')['passed']
    assert read(W/'models/train08_en/result.json')['optimizer_steps_completed']==4000
    assert not (W/'protocol/selected_final_round02_english.json').exists()
    subprocess.run(['wsl','-d','Ubuntu-22.04','--exec','/bin/true'],check=True,timeout=30)
    lock_check()
    for suite,expected in [('dev',8),('stress',16),('regression',5),('known_failure',1)]:
        py(suite,'run_round02_english.py',suite,'--candidate',CANDIDATE)
        summary=read(W/'runs'/(suite+'_'+CANDIDATE)/'summary.json')
        assert summary['completed']==summary['planned']==expected
        passed=stress_pass(summary) if suite=='stress' else summary['successes']==expected
        py(suite+'_rescore','verify_suite_records.py','--suite',suite+'_'+CANDIDATE)
        py(suite+'_phase_diagnostic','phase_diagnostics.py','--suite',suite+'_'+CANDIDATE)
        py(suite+'_failures','failure_details.py','--suite',suite+'_'+CANDIDATE)
        if not passed:
            collect_evidence()
            status('development_review',failed_suite=suite,successes=summary['successes'],planned=expected,fresh_final_evaluation_not_started=True,automatic_retraining=False);return
    py('select','run_round02_english.py','select','--candidate',CANDIDATE)
    py('heldout','run_round02_english.py','heldout','--candidate',CANDIDATE)
    run('render_probe',[BLENDER,'--factory-startup','--background','--python',str(W/'scripts/render_probe_round02_english.py')])
    py('probe_inference','run_probe_round02_english.py')
    run('probe_figures',[PLOT,'-X','utf8',str(W/'scripts/plot_probe_round02_english.py')])
    py('round_summary','round_summary.py','--suite','heldout_round02_english_'+CANDIDATE,'--protocol','protocol/round02_english.json')
    collect_evidence()
    flight=read(W/'reports'/('heldout_round02_english_'+CANDIDATE+'_round_summary.json'))
    probe=next(r for r in read(W/'probe_round02_english/outputs/summary.json')['summary'] if r['model']=='v1.1')
    status('evidence_ready',flight_gate_met=flight['flight_round_gate_met'],color_gate_met=probe['correct_goal']>=60 and probe['whole_quartet_correct']>=14,documents_and_final_audit_pending=True,automatic_retraining=False,published=False)

if __name__=='__main__':
    try:main()
    except BaseException as exc:status('pipeline_error',error=repr(exc),recovery='startup01');raise
