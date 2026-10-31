"""Offline evidence verification; never launches policy inference or changes records."""
import argparse, json, tempfile
from pathlib import Path
import numpy as np
from verify_records_round02_english import load_scorers,verify_one,scene_path,sha,read,W

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--partial',action='store_true');args=ap.parse_args()
    plan=read(W/'protocol/control_v11_final.json');root=W/'runs/control_v11_final'
    scorers=load_scorers();results=[];audits=[];pending=[]
    allowed={r[2] for r in read(W/'data/dataset04_en/manifest.json')['prompt_variants']}
    tempbase=W/'verification_tmp';tempbase.mkdir(exist_ok=True)
    for case in plan['cases']:
        folder=root/(case['id']+'_'+case['model']);source=folder/'record'
        if not (folder/'outcome.json').exists():pending.append(case);continue
        outcome=read(folder/'outcome.json');assert not outcome.get('error'),outcome
        manifest=read(folder/'manifest.json');scene=scene_path(case)
        assert sha(scene)==manifest['physics_sha256']
        assert manifest['runtime_lock_sha256']==plan['runtime_lock_sha256']
        assert manifest['runner_script_sha256']==plan['scripts']['run_suite_control_v11.py']
        with tempfile.TemporaryDirectory(prefix='control_',dir=tempbase) as tmp:
            results.append(verify_one(source,scene,case['kind']=='search',Path(tmp),scorers))
        events=read(source/'vla_link_events.json');inferences=[r for r in events if r['event']=='inference']
        assert inferences and {r['instruction'] for r in inferences}.issubset(allowed)
        assert {r['checkpoint_sha256'] for r in inferences}=={manifest['checkpoint_sha256']}
        usage=read(folder/'resource_usage.json');limits=read(folder/'resource_limits.json');m=usage['measurements']
        q,period=map(int,m['cpu.max'].split());assert q/period<=4 and int(m['memory.max'])<=8*1024**3
        assert limits['nice']>=10 and usage['exit']==0
        phases={};direct=stationary=disarmed=remembered=0;max_norm=0.
        with (source/'trace.jsonl').open(encoding='utf-8') as f:
            for line in f:
                r=json.loads(line);h=r.get('horizontal_control')
                if not h:continue
                assert h['controller_revision']=='control_v11'
                raw=np.asarray(h['raw_requested_forward_left']);adopted=np.asarray(h['adopted_requested_forward_left'])
                assert np.allclose(raw,r['model_action'][:2],rtol=0,atol=1e-10)
                norm=float(np.linalg.norm(raw));expected=raw*(min(1,.2/norm) if norm else 1)
                reason=h['execution_reason'];phases.setdefault(r['phase'],{});phases[r['phase']][reason]=phases[r['phase']].get(reason,0)+1
                if reason=='vla_velocity_request':
                    assert np.allclose(adopted,expected,rtol=0,atol=1e-10);direct+=1
                else:
                    assert np.all(adopted==0)
                    if reason=='disarmed':disarmed+=1
                    elif reason=='explicit_stationary_request':stationary+=1
                    else:raise AssertionError(reason)
                max_norm=max(max_norm,float(np.linalg.norm(adopted)));assert max_norm<=.2+1e-10
                stop=r.get('stop_intent_evidence')
                if stop and stop['source']=='remembered_intent_only':
                    assert stop['old_request_executed'] is False and stop['elapsed_since_policy_s']<=.5
                    remembered+=1
        audits.append(dict(record=folder.relative_to(W).as_posix(),checkpoint_sha256=manifest['checkpoint_sha256'],
                           actual_instructions=sorted({r['instruction'] for r in inferences}),inferences=len(inferences),
                           raw_to_adopted_velocity_verified=True,direct_vla_trace_rows=direct,stationary_override_rows=stationary,
                           disarmed_rows=disarmed,remembered_stop_intent_rows=remembered,phase_execution_counts=phases,
                           max_adopted_horizontal_speed=max_norm,wsl_cpu_limit=q/period,wsl_memory_limit=int(m['memory.max']),
                           peak_bytes=int(m['memory.peak']),trace_sha256=sha(source/'trace.jsonl'),
                           inference_log_sha256=sha(source/'vla_link_events.json'),resource_usage_sha256=sha(folder/'resource_usage.json')))
        print(json.dumps(dict(case=case['id'],model=case['model'],success=outcome['success'],verified=True)),flush=True)
    if not args.partial:assert len(results)==42 and not pending
    completed=len(results)==42 and not pending
    proof=dict(evidence_consistent=True,complete=completed,records=len(results),cases=results,
               scope='Independent replay scoring of existing records only; no flight or inference; original files unchanged.')
    execution=dict(passed=completed,cases=audits,pending=pending,
                   scope='Actual request, adopted horizontal velocity, model hash and WSL resource audit. No change to frozen implementation.')
    (W/'reports/control_v11_records_verified.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    (W/'reports/control_v11_execution_audit.json').write_text(json.dumps(execution,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=len(results),complete=completed)))
if __name__=='__main__':main()
