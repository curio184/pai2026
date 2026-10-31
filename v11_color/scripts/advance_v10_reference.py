"""Wait for original fixed evidence, then run the preregistered compatibility reference."""
import datetime,json,subprocess,sys,time
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def run(name,*args):
    print('START',name,flush=True);subprocess.run([sys.executable,'-B','-X','utf8',str(W/'scripts'/name),*args],check=True)
def main():
    marker=W/'ALL_TRIALS_REBUILD03.md'
    while not marker.exists():
        deadline=datetime.datetime.fromisoformat('2026-10-31T02:01:14+00:00')
        if (deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds()<5400:raise RuntimeError('Deadline reserve; no reference launched')
        time.sleep(2)
    r=json.loads((W/'results/all_trials_rebuild03.json').read_text(encoding='utf-8'))
    assert r['completed']==42 and r['all_new_records_independently_rescored']
    assert json.loads((W/'reports/rebuild03_v10_decoder_preflight.json').read_text())['passed']
    run('run_v10_teacher_reference.py')
    run('audit_v10_teacher_reference.py','rebuild03_v10_reference','--output','rebuild03_v10_reference_verified.json')
    run('merge_v10_reference_results.py')
    run('trial_index_rebuild03.py')
    run('verify_rebuild_timing.py','--final')
    print('REFERENCE_AND_EVIDENCE_COMPLETE',flush=True)
if __name__=='__main__':main()
