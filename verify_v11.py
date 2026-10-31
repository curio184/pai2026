"""Re-score the 26 final flights of v1.1 from their saved records.

Requires Python 3.11+ and NumPy only. No GPU, simulator, Blender or model weights.
Download v11_flight_records.zip from the v1.1.0 release, extract it, and pass the folder:

    python verify_v11.py --records <extracted folder>

Each record is copied to a temporary folder (saved scores removed) and scored again with the
same scorer used in the experiment (v11_color/scripts/score_rebuild05.py). The recomputed
success and stop durations are compared with the scores saved in this repository.
Original files are never modified. This checks the scoring, not a new flight.
"""
import argparse,contextlib,importlib.util,io,json,os,shutil,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;W=ROOT/'v11_color'
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def scene_for(case):
    s=case['scene']
    if case['kind']!='search':return W/'scenes/primitive_regression/physics/rescue_scene.xml'
    if s.startswith(('heldout','dev')):return W/'scenes'/s/'physics/rescue_scene.xml'
    if s=='known_swapped':return W/'scenes/known_swapped/physics/rescue_scene.xml'
    return ROOT/'rescue_search/scenes'/s/'physics/rescue_scene.xml'
def hold(score,case):
    color=case.get('color') or (case.get('profile') if case.get('profile') in ('blue','red') else None)
    g=score.get('goal_holds',{}).get(color) if color else None
    return round(g['physical_hold']['duration_s'],3) if g else None
def main(a):
    os.environ['RESCUE_PROJECT_ROOT']=str(ROOT);sys.path.insert(0,str(ROOT))
    scorer=load(W/'scripts/score_rebuild05.py','score_rebuild05')
    plan=json.loads((W/'protocol/rebuild05_final.json').read_text(encoding='utf-8'))
    src_root=Path(a.records)/'v11_color/runs/rebuild05_final';assert src_root.is_dir(),f'Not found: {src_root}'
    results=[]
    with tempfile.TemporaryDirectory(prefix='pai2026_v11_verify_') as temp:
        for case in plan['cases']:
            src=src_root/case['id']/'record';dst=Path(temp)/case['id']/'record'
            shutil.copytree(src,dst,ignore=shutil.ignore_patterns('physical_score.json','physical_score_original_contract.json','search_score.json'))
            search=case['kind']=='search'
            with contextlib.redirect_stdout(io.StringIO()):verdict=scorer.audit(dst,scene_for(case),search)
            saved_dir=W/'runs/rebuild05_final'/case['id']/'record'
            saved=json.loads((saved_dir/('search_score.json' if search else 'physical_score.json')).read_text(encoding='utf-8'))
            new_phys=json.loads((dst/'physical_score.json').read_text(encoding='utf-8'))
            old_phys=json.loads((saved_dir/'physical_score.json').read_text(encoding='utf-8'))
            row=dict(case=case['id'],group=case['group'],success=bool(verdict['success']),saved_success=bool(saved['success']),
                     hold_s=hold(new_phys,case),saved_hold_s=hold(old_phys,case))
            row['matches']=row['success']==row['saved_success'] and row['hold_s']==row['saved_hold_s']
            results.append(row)
    held=[r for r in results if r['group']=='matched_unseen']
    report=dict(all_match=all(r['matches'] for r in results),heldout_success=f"{sum(r['success'] for r in held)}/{len(held)}",
                video_scene_success=f"{sum(r['success'] for r in results if r['group']=='video_regression')}/9",
                cases=results,scope='Offline re-scoring of saved records; not a new flight or model inference',original_records_modified=False)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report['all_match']:raise SystemExit('Mismatch between recomputed and saved scores')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--records',required=True,help='Folder extracted from v11_flight_records.zip')
    main(p.parse_args())
