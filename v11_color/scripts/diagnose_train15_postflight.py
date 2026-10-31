"""Offline diagnosis of saved development runs, with the registered teacher.

Simulator truth is used only here, after flight, to reconstruct training targets.
No new inference, runtime modification, trial selection, or acceptance change.
"""
import argparse,bisect,datetime,hashlib,json,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent;sys.path.insert(0,str(P))
from make_revision_data import rotation,SCALE,scene_targets
from teacher_flight15 import teacher_chunk
from verify_records_round02_english import scene_path

def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--suite',default='stress_train15_en');a=ap.parse_args()
    suite=W/'runs'/a.suite;summary=read(suite/'summary.json');assert summary['completed']==summary['planned']
    assert a.suite.endswith('_train15_en'), 'Teacher15 can diagnose only candidate14 development records'
    assert not a.suite.startswith('heldout'), 'This diagnostic is for exposed development cases only'
    implementation_path=W/'protocol/train15_english_implementation.json'
    implementation=read(implementation_path)
    assert sha(W/'protocol/train15_english.json')==implementation['plan_sha256']
    for name,expected in implementation['scripts'].items():
        assert sha(W/'scripts'/name)==expected, name
    assert sha(W/'data/dataset15_en/audit.json')==implementation['dataset_audit_sha256']
    candidate_result=read(W/'models/train15_en/result.json')
    assert candidate_result['optimizer_steps_completed']==6000 and candidate_result['checkpoint']=='final'
    manifest=read(W/'data/dataset15_en/manifest.json')
    tasks={variants[2]:i for i,variants in enumerate(manifest['prompt_variants'])}
    assert manifest['braking_coefficient']==.6 and manifest['teacher_standoff_m']==1.0
    assert manifest['yaw_cap_rad_s']==.25 and manifest['yaw_capture_lookahead_s']==1.0
    assert manifest['navigation_yaw_cap_rad_s']==.25 and manifest['navigation_yaw_deadband_rad']==.05
    assert manifest['navigation_lookahead_s']==1.0
    rows=[]
    for outcome in summary['cases']:
        case=outcome['case'];rec=suite/(case['id']+'_'+case['model'])/'record'
        run_manifest=read(rec.parent/'manifest.json')
        assert run_manifest['checkpoint_sha256']==candidate_result['checkpoint_sha256']
        if not (rec/'vla_link_events.json').exists():continue
        target=scene_targets(scene_path(case))
        trace=[json.loads(x) for x in (rec/'trace.jsonl').read_text().splitlines()]
        times=[r['t'] for r in trace];by_capture={};groups={}
        for e in read(rec/'vla_link_events.json'):
            if e.get('event')!='inference':continue
            assert e['checkpoint_sha256']==candidate_result['checkpoint_sha256']
            state=np.asarray(e['estimated_state'],dtype=float);task=tasks[e['instruction']]
            index=min(bisect.bisect_left(times,e['sim_time_capture']),len(trace)-1)
            if index and abs(times[index-1]-e['sim_time_capture'])<abs(times[index]-e['sim_time_capture']):index-=1
            t=trace[index];qpos=np.asarray(t['truth'][19:26],dtype=float)
            reference=teacher_chunk(task,qpos,state,target,rotation,SCALE)*SCALE
            actual=np.asarray(e['action_chunk'],dtype=float)
            item=dict(id=e['id'],image_file=e['image_file'],capture_s=e['sim_time_capture'],
                phase=t['phase'],task=task,own=state.tolist(),
                mean_predicted_first10=actual[:10].mean(axis=0).tolist(),
                mean_teacher_first10=reference[:10].mean(axis=0).tolist(),
                absolute_error_first10=np.abs(actual[:10]-reference[:10]).mean(axis=0).tolist())
            groups.setdefault(t['phase'],[]).append(item)
            by_capture[e['sim_time_capture']]=(reference,task)
        phases={}
        for phase,items in groups.items():
            executed=[]
            for t in trace:
                if t['phase']!=phase or t.get('action_source')!='policy':continue
                pair=by_capture.get(t.get('model_capture_time'))
                if pair is None:continue
                ref,task=pair;k=int(t['chunk_index']);assert 0<=k<len(ref)
                action=np.asarray(t['model_action'],dtype=float)
                reference=ref[k].copy()
                yaw_k=t.get('yaw_chunk_index');yaw_k=k if yaw_k is None else int(yaw_k)
                assert 0<=yaw_k<len(ref)
                reference[3]=ref[yaw_k,3]
                executed.append((action,reference,np.asarray(t['estimated_state']),k))
            phases[phase]=dict(images=len(items),start_s=items[0]['capture_s'],end_s=items[-1]['capture_s'],
                predicted_first10_median=np.median([r['mean_predicted_first10'] for r in items],axis=0).tolist(),
                teacher_first10_median=np.median([r['mean_teacher_first10'] for r in items],axis=0).tolist(),
                error_first10_median=np.median([r['absolute_error_first10'] for r in items],axis=0).tolist(),
                largest_horizontal_errors=sorted(items,key=lambda r:np.linalg.norm(r['absolute_error_first10'][:2]),reverse=True)[:3])
            if executed:
                acts=np.stack([x[0] for x in executed]);refs=np.stack([x[1] for x in executed]);states=np.stack([x[2] for x in executed])
                phases[phase]['actual_execution']=dict(samples=len(executed),
                    median_action=np.median(acts,axis=0).tolist(),median_teacher=np.median(refs,axis=0).tolist(),
                    median_absolute_error=np.median(np.abs(acts-refs),axis=0).tolist(),
                    median_own=np.median(states,axis=0).tolist(),
                    chunk_index_min_median_max=np.percentile([x[3] for x in executed],[0,50,100]).tolist())
        score=read(rec/('search_score.json' if case['kind']=='search' else 'physical_score.json'))
        physical=score['physical'] if case['kind']=='search' else score
        color=case.get('color',case.get('profile'));result=read(rec/'result.json')
        rows.append(dict(id=case['id'],success=outcome['success'],color=color,
            failure=result.get('mission_failure'),stop_reason=result['stop_reason'],
            goal_hold_s=physical['goal_holds'][color]['physical_hold']['duration_s'] if color in ['blue','red'] else None,
            initial_hover_s=physical['explicit_hover_instruction_hold']['duration_s'],
            minimum_person_clearance_m=physical['minimum_person_clearance_m'],phases=phases,
            events_sha256=sha(rec/'vla_link_events.json'),trace_sha256=sha(rec/'trace.jsonl')))
    out=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),suite=a.suite,
        completed=len(rows),planned=summary['planned'],teacher_source_sha256=sha(W/'scripts/teacher_flight15.py'),
        implementation_sha256=sha(implementation_path), dataset_audit_sha256=implementation['dataset_audit_sha256'],
        trained_checkpoint_sha256=candidate_result['checkpoint_sha256'],
        diagnostic_script_sha256=sha(Path(__file__)),
        scope='Saved development records only. Truth used postflight to reconstruct teacher labels. No policy inference or changes to trials.',
        caveat='Teacher reconstruction is a diagnostic, not a causal attribution or a new success criterion. First10 summaries differ from the delayed chunks actually executed.',cases=rows)
    dest=W/'reports'/(a.suite+'_postflight_development_diagnostic.json');assert not dest.exists();dest.write_text(json.dumps(out,indent=2),encoding='utf8')
    print(json.dumps(dict(report=str(dest),completed=len(rows),failures=[{k:r[k] for k in ['id','failure','stop_reason','goal_hold_s','initial_hover_s']} for r in rows if not r['success']])))
if __name__=='__main__':main()
