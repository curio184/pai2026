"""Independently replay the fixed navfocus records; no inference or flight."""
import argparse,contextlib,hashlib,io,json,shutil,tempfile
from pathlib import Path
import numpy as np
from verify_records_round02_english import scene_path,W
from score_navfocus import audit
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def expected_hash(path,digest):
    actual=sha(path)
    if actual==digest:return True
    provenance=W/'PUBLICATION_PROVENANCE.json'
    if not provenance.exists():return False
    rel=path.relative_to(W.parent).as_posix()
    return any(r['path']==rel and r['original_sha256']==digest and r['distributed_sha256']==actual and r['path_redaction_only'] for r in read(provenance)['files'])
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--partial',action='store_true');parser.add_argument('--no-write',action='store_true');args=parser.parse_args()
    plan=read(W/'protocol/navfocus_receipt.json');root=W/'runs/navfocus_receipt';results=[];execution=[];pending=[]
    tempbase=W/'verification_tmp';tempbase.mkdir(exist_ok=True)
    allowed={r[2] for r in read(W/'data/dataset04_en/manifest.json')['prompt_variants']}
    for case in plan['cases']:
        folder=root/(case['id']+'_'+case['model']);source=folder/'record'
        if not (folder/'outcome.json').exists():pending.append(case);continue
        out=read(folder/'outcome.json');assert not out.get('error'),out
        manifest=read(folder/'manifest.json');scene=scene_path(case)
        assert expected_hash(scene,manifest['physics_sha256'])
        assert manifest['runtime_lock_sha256']==plan['runtime_lock_sha256']
        assert manifest['runner_script_sha256']==plan['scripts']['run_suite_receipt.py']
        hashes={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
        expected=read(source/('search_score.json' if case['kind']=='search' else 'physical_score.json'))
        with tempfile.TemporaryDirectory(prefix='navfocus_',dir=tempbase) as tmp:
            dest=Path(tmp)/'record'
            shutil.copytree(source,dest,ignore=shutil.ignore_patterns('physical_score.json','physical_score_original_contract.json','search_score.json','*.BIN','*.bin','logs'))
            with contextlib.redirect_stdout(io.StringIO()):actual=audit(dest,scene,case['kind']=='search')
            assert actual==expected,(case,'replay differs')
            assert read(dest/'physical_score_original_contract.json')==read(source/'physical_score_original_contract.json')
        assert all(sha(source/n)==h for n,h in hashes.items())
        links=[r for r in read(source/'vla_link_events.json') if r['event']=='inference']
        assert links and {r['instruction'] for r in links}.issubset(allowed)
        assert {r['checkpoint_sha256'] for r in links}=={manifest['checkpoint_sha256']}
        usage=read(folder/'resource_usage.json');m=usage['measurements'];q,period=map(int,m['cpu.max'].split())
        assert q/period<=4 and int(m['memory.max'])<=8*1024**3 and usage['exit']==0
        physical=read(source/'physical_score.json')
        target=case.get('color',case.get('profile'))
        hold=physical['goal_holds'].get(target,{}).get('physical_hold')
        hold_span=None if not hold or hold['end_s'] is None else (hold['end_s']-hold['duration_s'],hold['end_s'])
        nav=primitive=remembered=hold_rows=hold_transition_rows=0;owners={};owner_hold_start=None;owner_hold_s=0.
        with (source/'trace.jsonl').open(encoding='utf-8') as f:
            for line in f:
                r=json.loads(line);owner=(r.get('execution_owner') or {}).get('owner');h=r.get('horizontal_control')
                if hold_span and hold_span[0]<=r['t']<=hold_span[1]:
                    assert r['phase']==target,'Scored target stop must occur during approach, not later primitive hover'
                    if owner=='VLA':
                        hold_rows+=1
                        if owner_hold_start is None:owner_hold_start=r['t']
                        owner_hold_s=max(owner_hold_s,r['t']-owner_hold_start)
                    else:
                        # The phase label changes before the next 20Hz control tick.
                        # Do not credit transition rows to the VLA-only duration.
                        hold_transition_rows+=1;owner_hold_start=None
                if not h:continue
                assert h['controller_revision']=='control_v11' # unchanged horizontal PI module
                assert np.allclose(h['raw_requested_forward_left'],r['model_action'][:2],rtol=0,atol=1e-10)
                if owner:owners[owner]=owners.get(owner,0)+1
                if owner=='VLA':
                    assert np.array_equal(r['model_action'][:4],r['adopted_action'][:4]);nav+=1
                    raw=np.asarray(r['model_action'][:2]);norm=float(np.linalg.norm(raw));wanted=raw*(min(1,.2/norm) if norm else 1)
                    assert np.allclose(h['adopted_requested_forward_left'],wanted,rtol=0,atol=1e-10)
                elif owner=='mission_primitive':
                    assert np.all(np.asarray(h['adopted_requested_forward_left'])==0);primitive+=1
                stop=r.get('stop_intent_evidence')
                if stop and stop['source']=='remembered_intent_only':assert stop['old_request_executed'] is False;remembered+=1
        if actual['success'] and target in ('blue','red'):assert owner_hold_s>=3.,('VLA-only target hold below three seconds',case,owner_hold_s)
        results.append(dict(record=folder.relative_to(W).as_posix(),flight_success=actual['success'],score_matches=True,legacy_contract_score_matches=True,original_unchanged=True,scene_sha256=sha(scene)))
        execution.append(dict(record=folder.relative_to(W).as_posix(),checkpoint_sha256=manifest['checkpoint_sha256'],
             actual_instructions=sorted({r['instruction'] for r in links}),inferences=len(links),nav_four_components_preserved=True,
             navigation_trace_rows=nav,primitive_trace_rows=primitive,owners=owners,remembered_stop_intent_rows=remembered,
             scored_target_hold_vla_rows=hold_rows,scored_target_hold_transition_rows=hold_transition_rows,
             continuous_vla_only_hold_s=owner_hold_s,scored_target_hold_excludes_later_primitive_hover=True,
             wsl_cpu_limit=q/period,wsl_memory_limit=int(m['memory.max']),peak_bytes=int(m['memory.peak']),
             trace_sha256=sha(source/'trace.jsonl'),inference_log_sha256=sha(source/'vla_link_events.json')))
        print(json.dumps(dict(case=case['id'],model=case['model'],success=out['success'],verified=True)),flush=True)
    if not args.partial:assert len(results)==42 and not pending
    complete=len(results)==42 and not pending
    if not args.no_write:
        (W/'reports/receipt_records_verified.json').write_text(json.dumps(dict(evidence_consistent=True,complete=complete,records=len(results),cases=results),indent=2),encoding='utf-8')
        (W/'reports/receipt_execution_audit.json').write_text(json.dumps(dict(passed=complete,cases=execution,pending=pending),indent=2),encoding='utf-8')
    print(json.dumps(dict(records=len(results),complete=complete)))
if __name__=='__main__':main()
