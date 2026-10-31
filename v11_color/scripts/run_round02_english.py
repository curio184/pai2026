"""Round-2 orchestration only; use the frozen flight runner and scorers."""
import argparse,datetime,json,shutil
from pathlib import Path
from run_suite_english import W,P,sha,write,run_case
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def stress_pass(summary):
    rows=summary['cases']
    if summary['completed']!=16 or summary['planned']!=16:return False
    if sum(r['success'] for r in rows)<14:return False
    for color in ['blue','red']:
        if sum(r['success'] for r in rows if r['case']['color']==color)<7:return False
    for scene in {r['case']['scene'] for r in rows}:
        if sum(r['success'] for r in rows if r['case']['scene']==scene)<3:return False
    return True
def select(candidate):
    roundplan=read(W/'protocol/round02_english.json');trained=read(W/'models'/candidate/'result.json')
    assert trained['selection']=='Final step only'
    summaries={name:read(W/'runs'/(name+'_'+candidate)/'summary.json') for name in ['dev','stress','regression','known_failure']}
    assert summaries['dev']['completed']==summaries['dev']['successes']==8
    assert stress_pass(summaries['stress'])
    assert summaries['regression']['completed']==summaries['regression']['successes']==5
    assert summaries['known_failure']['completed']==summaries['known_failure']['successes']==1
    assert not (W/'protocol/selected_final_round02_english.json').exists()
    assert not list((W/'runs').glob('heldout_round02_*')) and not (W/'probe_round02_english/outputs').exists()
    write(W/'protocol/selected_final_round02_english.json',dict(candidate=candidate,checkpoint_sha256=trained['checkpoint_sha256'],
        selection='Final step; preregistered development, exposed stress, regression and known-failure gates. No round-2 policy inference or flight yet.',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),round_protocol_sha256=sha(W/'protocol/round02_english.json'),
        summary_sha256={name:sha(W/'runs'/(name+'_'+candidate)/'summary.json') for name in summaries}))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('suite',choices=['dev','stress','regression','known_failure','select','heldout']);parser.add_argument('--candidate',default='train04_en');a=parser.parse_args()
    if a.suite=='select':select(a.candidate);return
    base=read(W/'protocol/plan.json');plan=read(W/'protocol/round02_english.json')
    trained=read(W/'models'/a.candidate/'result.json');assert trained['selection']=='Final step only'
    checkpoint=W/'models'/a.candidate/'final';assert sha(checkpoint/'model.safetensors')==trained['checkpoint_sha256']
    cases=[]
    if a.suite=='dev':
        for layout in base['development_layouts']:
            for color in ['blue','red']:cases.append(dict(id=layout['name']+'_'+color,kind='search',scene=layout['name'],color=color,model='v1.1'))
        for profile in ['blue','red','turns','left']:cases.append(dict(id='primitive_'+profile,kind='primitive',scene='clear',profile=profile,model='v1.1'))
    elif a.suite=='stress':cases=plan['development_stress_cases']
    elif a.suite=='regression':
        for scene,color in [('clear','blue'),('clear','red'),('fog_light','blue'),('fog_dense','blue'),('dust','blue')]:cases.append(dict(id=scene+'_'+color,kind='search',scene=scene,color=color,model='v1.1'))
    elif a.suite=='known_failure':cases=[dict(id='T3_blue_retest',kind='search',scene='known_swapped',color='blue',model='v1.1')]
    else:
        chosen=read(W/'protocol/selected_final_round02_english.json');assert chosen['candidate']==a.candidate and chosen['checkpoint_sha256']==trained['checkpoint_sha256']
        for i,case in enumerate(plan['heldout_cases']):
            for model in (['v1.0','v1.1'] if i%2==0 else ['v1.1','v1.0']):cases.append(dict(**case,kind='search',model=model,jitter=True))
    for c in cases:c['round_protocol_sha256']=sha(W/'protocol/round02_english.json')
    name=('heldout_round02_english' if a.suite=='heldout' else a.suite)+'_'+a.candidate
    suite=W/'runs'/name;suite.mkdir(parents=True,exist_ok=True)
    meta=dict(cases=cases,checkpoint_sha256=trained['checkpoint_sha256'],round_protocol_sha256=sha(W/'protocol/round02_english.json'),
        base_protocol_sha256=sha(W/'protocol/plan.json'),script_sha256=sha(Path(__file__)),frozen_runner_sha256=sha(W/'scripts/run_suite_english.py'),runtime_lock_sha256=sha(W/'protocol/runtime_english_lock.json'))
    if (suite/'suite_plan.json').exists():assert read(suite/'suite_plan.json')==meta
    else:write(suite/'suite_plan.json',meta)
    outcomes=[]
    for c in cases:
        if shutil.disk_usage(W).free<5*1024**3:raise RuntimeError('Disk reserve reached; consult before any move')
        folder=suite/(c['id']+'_'+c['model'])
        if folder.exists():
            if not (folder/'outcome.json').exists():raise RuntimeError('Incomplete attempt; no automatic retry: '+str(folder))
            outcome=read(folder/'outcome.json')
        else:outcome=run_case(c,checkpoint if c['model']=='v1.1' else P/base['training']['initial_checkpoint'],folder)
        outcomes.append(outcome);write(suite/'summary.json',dict(completed=len(outcomes),planned=len(cases),successes=sum(o['success'] for o in outcomes),cases=outcomes))
        if outcome.get('error'):raise RuntimeError('Infrastructure failure retained: '+str(folder))
if __name__=='__main__':main()
