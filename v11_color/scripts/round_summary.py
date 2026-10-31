"""Summarize one fixed evaluation round; never pool models across revisions."""
import argparse,hashlib,json,math
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def interval(k,n):
    if not n:return None
    z=1.959963984540054;d=1+z*z/n;c=(k/n+z*z/(2*n))/d
    r=z*math.sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/d
    return [c-r,c+r]
def main():
    a=argparse.ArgumentParser();a.add_argument('--suite',required=True);a.add_argument('--protocol',default='protocol/plan.json');a.add_argument('--allow-incomplete',action='store_true');args=a.parse_args()
    folder=W/'runs'/args.suite;protocol=W/args.protocol;plan=read(protocol);sp=read(folder/'suite_plan.json')
    assert plan['success_gate']['heldout_total']=='at least 14/16'
    assert plan['success_gate']['per_color']=='at least 7/8'
    assert plan['success_gate']['per_layout']=='at least 3/4'
    cases=sp['cases'];assert len(cases)==32
    keys=[(c['id'],c['model']) for c in cases];assert len(set(keys))==32
    planned={(c['id'],m):c for c in plan['heldout_cases'] for m in ['v1.0','v1.1']}
    assert set(planned)==set(keys)
    outcomes=[];missing=[]
    for c in cases:
        for k,v in planned[c['id'],c['model']].items():assert c[k]==v,(c['id'],k)
        p=folder/(c['id']+'_'+c['model'])/'outcome.json'
        if not p.exists():missing.append(c);continue
        o=read(p);assert o['case']==c
        outcomes.append(dict(case=c,success=bool(o['success']),error=o.get('error'),outcome_path=p.relative_to(W).as_posix(),outcome_sha256=sha(p)))
    if not args.allow_incomplete:assert not missing
    statistics=[]
    for model in ['v1.0','v1.1']:
        for group,value in [('all',None),('color','blue'),('color','red')]+[('scene',l['name']) for l in plan['heldout_layouts']]:
            rr=[r for r in outcomes if r['case']['model']==model and (group=='all' or r['case'][group]==value)]
            k=sum(r['success'] for r in rr);n=len(rr)
            statistics.append(dict(model=model,group=group,value=value,k=k,n=n,wilson95=interval(k,n)))
    v=[s for s in statistics if s['model']=='v1.1']
    gate=not missing and v[0]['n']==16 and v[0]['k']>=14 and all(s['n']==8 and s['k']>=7 for s in v if s['group']=='color') and all(s['n']==4 and s['k']>=3 for s in v if s['group']=='scene')
    report=dict(suite=args.suite,protocol_sha256=sha(protocol),suite_plan_sha256=sha(folder/'suite_plan.json'),
        checkpoint_sha256=sp['checkpoint_sha256'],complete=not missing,completed=len(outcomes),planned=32,
        all_outcomes=outcomes,not_yet_completed=missing,statistics=statistics,flight_round_gate_met=bool(gate),
        scope='This evaluation round only. Regression, static counterfactual and known-failure replay gates are separate. No earlier failed round is pooled or discarded.')
    dest=W/'reports'/(args.suite+'_round_summary.json');dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(suite=args.suite,completed=len(outcomes),complete=not missing,gate=bool(gate),statistics=statistics)))
if __name__=='__main__':main()
