"""Verify recorded VLA-plan conversion algebra, raw outputs and unchanged physics scores.

This is offline evidence checking. Truth is not used by the online tracker.
"""
import argparse,contextlib,hashlib,io,json,shutil,sys,tempfile
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(W/'runtime_rebuild03_v10ref'))
from plan_endpoint import decode_plan_endpoint
from plan_tracker import rotation
from score_rebuild03 import audit
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(folder):
    manifest=read(folder/'manifest.json');outcome=read(folder/'outcome.json');case=outcome['case']
    ready=read(folder/'worker_ready.json')
    if folder.parent.name!='rebuild03_dev' or case['kind']=='search':assert ready['num_steps']==5
    rec=folder/'record';hashes={p.relative_to(rec).as_posix():sha(p) for p in rec.rglob('*') if p.is_file()}
    from verify_records_round02_english import scene_path
    scene=scene_path(case)
    assert expected_hash(scene,manifest['physics_sha256'])
    tempbase=W/'reports/rebuild_verify_tmp';tempbase.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tempbase) as tmp:
        dest=Path(tmp)/'record'
        shutil.copytree(rec,dest,ignore=shutil.ignore_patterns('physical_score.json','physical_score_original_contract.json','search_score.json','*.BIN','*.bin','logs'))
        with contextlib.redirect_stdout(io.StringIO()):scored=audit(dest,scene,case['kind']=='search')
        expected=read(rec/('search_score.json' if case['kind']=='search' else 'physical_score.json'))
        assert scored==expected,'Score replay mismatch'
        assert read(dest/'physical_score_original_contract.json')==read(rec/'physical_score_original_contract.json')
    packets={e['sim_time_capture']:e for e in read(rec/'vla_link_events.json') if e['event']=='inference'}
    decoded={};nav=0;fresh=0
    physical=read(rec/'physical_score.json');target=case.get('color',case.get('profile'))
    hold=physical['goal_holds'].get(target,{}).get('physical_hold')
    span=None if not hold or hold['end_s'] is None else (hold['end_s']-hold['duration_s'],hold['end_s'])
    hold_start=None;owned_hold=0.
    for e in packets.values():
        assert sha(rec/'observations'/e['image_file'])==e['image_sha256']
        assert e['checkpoint_sha256']==manifest['checkpoint_sha256']
        decoded[e['sim_time_capture']]=decode_plan_endpoint(e['action_chunk'],e['estimated_state'])
    for line in (rec/'trace.jsonl').open(encoding='utf-8'):
        row=json.loads(line);evidence=row.get('plan_tracking')
        if span and span[0]<=row['t']<=span[1]:
            valid=(row['phase']==target and evidence and evidence.get('owner')=='VLA_plan_tracker' and evidence.get('valid_plan') and row['action_source']=='policy')
            if valid:
                if hold_start is None:hold_start=row['t']
                owned_hold=max(owned_hold,row['t']-hold_start)
            else:hold_start=None
        if not evidence or evidence.get('owner')!='VLA_plan_tracker':continue
        nav+=1;assert evidence['truth_used'] is False
        assert np.array_equal(row['raw_model_action'],row['model_action'])
        if not evidence.get('valid_plan'):continue
        fresh+=1;packet=packets[evidence['packet_capture_s']]
        endpoint,details=decoded[evidence['packet_capture_s']]
        # Linux runtime vs Windows replay can differ by one floating-point ULP.
        assert details['unsaturated_estimates']==evidence['decode']['unsaturated_estimates']
        assert details['stop_planned']==evidence['decode']['stop_planned']
        for name in ['rollout_endpoint','endpoint_forward_left']:
            assert np.allclose(details[name],evidence['decode'][name],atol=1e-12,rtol=0)
        capture=evidence['capture'];endpoint_target=np.asarray(capture['odometry_ned'])+rotation(capture['yaw_ned'])@endpoint
        assert np.allclose(endpoint_target,capture['decoded_target_ned'],atol=1e-10,rtol=0)
        request=.8*np.asarray(evidence['remaining_forward_left_m'])-.5*np.asarray(row['estimated_state'][:2])
        norm=np.linalg.norm(request)
        if norm>.2:request*=.2/norm
        assert np.allclose(request,row['adopted_action'][:2],atol=1e-10,rtol=0)
        assert np.allclose(request,row['horizontal_control']['raw_requested_forward_left'],atol=1e-10,rtol=0)
        chunk=np.asarray(packet['action_chunk']);index=row['chunk_index'];yaw_index=row['yaw_chunk_index']
        selected=chunk[index].copy();selected[3]=chunk[yaw_index,3]
        selected[:2]=np.clip(selected[:2],-.2,.2);norm=np.linalg.norm(selected[:2])
        if norm>.2:selected[:2]*=.2/norm
        selected[2]=np.clip(selected[2],-.3,.3);selected[3]=np.clip(selected[3],-.35,.35)
        assert np.allclose(selected[:4],row['raw_model_action'][:4],atol=1e-7,rtol=0)
    usage=read(folder/'resource_usage.json')['measurements'];quota,period=map(int,usage['cpu.max'].split())
    assert quota/period<=4 and int(usage['memory.max'])<=8*1024**3
    if outcome['success'] and target in ['blue','red']:assert owned_hold>=3.,(case,owned_hold)
    assert all(sha(rec/n)==h for n,h in hashes.items())
    return dict(record=folder.relative_to(W).as_posix(),success=outcome['success'],independent_score_matches=True,
        original_records_unchanged=True,physical_thresholds_unchanged=True,navigation_rows=nav,
        verified_fresh_plan_rows=fresh,raw_vla_output_preserved_in_record=True,instantaneous_velocity_transformed=True,
        decoder_and_tracking_algebra_verified=True,continuous_fresh_vla_plan_stop_s=owned_hold,
        ws_cpu=quota/period,ws_memory_bytes=int(usage['memory.max']))
def expected_hash(path,digest):
    actual=sha(path)
    if actual==digest:return True
    provenance=W/'PUBLICATION_PROVENANCE.json'
    if not provenance.exists():return False
    rel=path.relative_to(W.parent).as_posix()
    return any(r['path']==rel and r['original_sha256']==digest and r['distributed_sha256']==actual and r['path_redaction_only'] for r in read(provenance)['files'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--no-write',action='store_true');a=p.parse_args()
    plan=read(W/'protocol/rebuild03_v10_reference.json');rows=[]
    for case in plan['cases']:
        folder=W/'runs/rebuild03_v10_reference'/(case['id']+'_'+case['model'])
        manifest=read(folder/'manifest.json');outcome=read(folder/'outcome.json')
        assert manifest['case']==outcome['case']==case
        assert expected_hash(W/'protocol/rebuild03_v10_reference.json',manifest['final_protocol_sha256'])
        assert expected_hash(W/'scripts/run_suite_rebuild03_v10ref.py',manifest['runner_script_sha256'])
        assert manifest['checkpoint_sha256']==plan['checkpoint_sha256' if case['model']=='v1.1' else 'old_checkpoint_sha256']
        row=verify(folder);rows.append(row);print(json.dumps(row),flush=True)
    assert len(rows)==16
    result=dict(records=16,all_verified=True,complete=True,cases=rows)
    if not a.no_write:(W/'reports/portable_v10_reference_verified.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=16,all_verified=True)))
if __name__=='__main__':main()
