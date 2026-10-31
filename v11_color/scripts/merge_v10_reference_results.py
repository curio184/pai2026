"""Add the full old-teacher reference without altering the frozen42-case verdict."""
import hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=W/'results/all_trials_rebuild03.json';r=read(p)
    assert 'reference_cases' not in r
    plan=read(W/'protocol/rebuild03_v10_reference.json')
    proof=read(W/'reports/rebuild03_v10_reference_verified.json')
    assert proof['all_verified'] and proof['records']==16
    rows=[]
    for case in plan['cases']:
        folder=W/'runs/rebuild03_v10_reference'/(case['id']+'_'+case['model'])
        o=read(folder/'outcome.json');m=read(folder/'manifest.json');sp=folder/'record/search_score.json';s=read(sp);phys=s['physical']
        assert o['case']==case and s['success']==o['success'] and not o.get('error')
        assert m['checkpoint_sha256']==plan['checkpoint_sha256']
        assert m['runtime_lock_sha256']==sha(W/'protocol/rebuild03_v10_reference.json')
        goal=phys['goal_holds'][case['color']]
        rows.append(dict(suite='rebuild03_v10_reference',case=case,record=folder.relative_to(W).as_posix(),success=o['success'],
            error=None,flight_started=True,checkpoint_sha256=m['checkpoint_sha256'],outcome_sha256=sha(folder/'outcome.json'),
            manifest_sha256=sha(folder/'manifest.json'),score_path=sp.relative_to(W).as_posix(),score_sha256=sha(sp),
            hold_s=goal['physical_hold']['duration_s'],min_goal_distance_m=goal['minimum_goal_distance_m'],
            min_person_clearance_m=phys['minimum_person_clearance_m']))
    stats=[]
    for group,key in [('all',None),('color','blue'),('color','red')]+[('layout',x['name']) for x in read(W/'protocol/rebuild_final_layouts.json')['heldout_layouts']]:
        rr=[x for x in rows if group=='all' or x['case']['color' if group=='color' else 'scene']==key]
        stats.append(dict(model='v1.0_teacher_reference',group=group,key=key,k=sum(x['success'] for x in rr),n=len(rr)))
    core=W/'results/all_trials_rebuild03_core.json';assert not core.exists();shutil.copy2(p,core)
    r.update(reference_cases=rows,reference_statistics=stats,reference_independently_rescored=True,
        reference_scope='Same old checkpoint, English,5 flow steps, tracking controller and physical criteria. Decoder uses old teacher gain.7/no velocity damping; both original common-decoder and semantic-compatible outcomes retained.',
        learning_attribution='Common-decoder results are not a pure training-effect estimate: teacher velocity semantics, instruction language and learned behavior differ. Raw-output color interventions do not use either decoder.',
        publication_evidence_complete=bool(r['preregistered_goal_met'] and len(rows)==16))
    r['all_executed_cases']+=rows
    assert len(r['all_executed_cases'])==454 and len({x['record'] for x in r['all_executed_cases']})==454
    p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(reference_successes=stats[0]['k'],reference_trials=16,all_trials=454,original_goal_met=r['preregistered_goal_met'])))
if __name__=='__main__':main()
