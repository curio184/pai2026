"""Recompute scores, including failed flights, without touching original records.

NumPy only. This verifies evidence consistency, not new model inference.
"""
import argparse,contextlib,hashlib,importlib.util,io,json,os,shutil,sys,tempfile
from pathlib import Path
W=Path(__file__).resolve().parents[1];P=W.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_scorers():
    os.environ['RESCUE_PROJECT_ROOT']=str(P);sys.path.insert(0,str(P))
    from score_mission import score
    file=W/'runtime/score_search.py'
    spec=importlib.util.spec_from_file_location('v11_score_search',file);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return score,mod.audit
def verify_one(source,scene,search,temporary,scorers):
    original_hashes={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
    dest=temporary/'record'
    shutil.copytree(source,dest,ignore=shutil.ignore_patterns('physical_score.json','search_score.json','*.BIN','*.bin','logs'))
    expected=read(source/('search_score.json' if search else 'physical_score.json'))
    with contextlib.redirect_stdout(io.StringIO()):actual=scorers[1 if search else 0](dest,scene)
    unchanged=all(sha(source/name)==h for name,h in original_hashes.items())
    result=dict(record=str(source),flight_success=actual['success'],score_matches=actual==expected,physical_score_recomputed=True,original_unchanged=unchanged,scene_sha256=sha(scene))
    if not result['score_matches'] or not unchanged:raise RuntimeError(json.dumps(result))
    return result
def scene_path(case):
    if case['kind']=='primitive':return W/'scenes/primitive_regression/physics/rescue_scene.xml'
    if case['scene']=='known_swapped':return W/'scenes/known_swapped/physics/rescue_scene.xml'
    if case['scene'].startswith(('dev','heldout')):return W/'scenes'/case['scene']/'physics/rescue_scene.xml'
    for root in [P/'rescue_search',P/'tmp/rescue_search']:
        candidate=root/'scenes'/case['scene']/'physics/rescue_scene.xml'
        if candidate.exists():return candidate
    raise FileNotFoundError(case['scene'])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prior-self-check',action='store_true');ap.add_argument('--output',type=Path);a=ap.parse_args()
    tempbase=W/'verification_tmp';tempbase.mkdir(exist_ok=True);scorers=load_scorers();results=[]
    if a.prior_self_check:
        jobs=[(P/'validation_v1_1/runs/T3_01/record',P/'validation_v1_1/scenes/swapped/physics/rescue_scene.xml',True)]
    else:
        report=read(W/'results/all_trials.json');jobs=[]
        for row in report['all_executed_cases']:
            if not row.get('score_path'):continue
            jobs.append((W/row['record']/'record',scene_path(row['case']),row['case']['kind']=='search'))
        if not jobs:raise RuntimeError('No completed records to verify')
    for source,scene,search in jobs:
        with tempfile.TemporaryDirectory(prefix='case_',dir=tempbase) as tmp:
            temporary=Path(tmp).resolve();assert temporary.is_relative_to(tempbase.resolve())
            results.append(verify_one(source,scene,search,temporary,scorers))
        print(json.dumps(results[-1],ensure_ascii=False),flush=True)
    report=dict(evidence_consistent=True,records=len(results),flight_successes=sum(r['flight_success'] for r in results),cases=results,scope='Offline scoring and file checks only; no new flight or inference',script_sha256=sha(Path(__file__)))
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(evidence_consistent=True,records=len(results),flight_successes=report['flight_successes'])))
if __name__=='__main__':main()
