"""Recover scoring only after stdlib failure; no repeated flight."""
import datetime,json,subprocess,sys
from pathlib import Path
from run_suite_receipt import W,sha,write,lock_check
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    lock_check();plan=read(W/'protocol/navfocus_receipt.json')
    for n,h in plan['scripts'].items():assert sha(W/'scripts'/n)==h,n
    root=W/'runs/navfocus_receipt';folder=root/'NFH07_v1.1';record=folder/'record'
    out=read(folder/'outcome.json');assert out['runner_exit']==0 and 'Scorer failed' in out['error']
    assert read(folder/'resource_usage.json')['exit']==0
    baseline={p.relative_to(record).as_posix():sha(p) for p in record.rglob('*') if p.is_file()}
    for name in ['outcome.json','scoring.log']:
        src=folder/name;dest=folder/(src.stem+'_before_environment_recovery'+src.suffix)
        with dest.open('xb') as f:f.write(src.read_bytes())
    scene=W/'scenes'/out['case']['scene']/'physics/rescue_scene.xml'
    with (folder/'scoring_recovery.log').open('x',encoding='utf-8') as log:
        done=subprocess.run([sys.executable,'-B','-X','utf8',str(W/'scripts/score_navfocus.py'),str(record),'--scene',str(scene),'--search'],stdout=log,stderr=subprocess.STDOUT)
    assert done.returncode==0
    assert all(sha(record/n)==h for n,h in baseline.items())
    verdict=read(record/'search_score.json')
    out['infrastructure_error_before_recovery']=out.pop('error');out.update(success=verdict['success'],checks=verdict['checks'],checkpoint_sha256=read(folder/'manifest.json')['checkpoint_sha256'],scoring_recovered_without_reflight=True)
    write(folder/'outcome.json',out)
    write(folder/'scoring_recovery_receipt.json',dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        original_records_sha256=baseline,original_records_unchanged=True,scorer_sha256=sha(W/'scripts/score_navfocus.py'),
        no_reflight=True,criteria_unchanged=True,environment_recovery='<WORK_ROOT>/runtimes/receipt_environment_recovery/recovery.json'))
    outcomes=[read(root/(c['id']+'_'+c['model'])/'outcome.json') for c in plan['cases'][:14]]
    assert len(outcomes)==14 and not any(r.get('error') for r in outcomes)
    write(root/'summary.json',dict(completed=14,planned=42,cases=outcomes,configuration='navfocus_receipt',protocol_sha256=sha(W/'protocol/navfocus_receipt.json')))
    print(json.dumps({'recovered_case':'NFH07_v1.1','success':out['success'],'completed':14,'remaining':28}))
if __name__=='__main__':main()
