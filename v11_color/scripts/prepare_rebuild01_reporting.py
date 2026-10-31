"""Prepare result readers; never runs flights or changes an acceptance threshold."""
from pathlib import Path
import ast
W=Path(__file__).resolve().parents[1]
def main():
    s=(W/'scripts/verify_probe_navfocus.py').read_text(encoding='utf-8')
    s=s.replace('navfocus_layouts.json','rebuild_final_layouts.json').replace('navfocus','rebuild01')
    # The unused historical specs assignment is harmless, but remove it to avoid ambiguity.
    start=s.index('    specs=');end=s.index("    specs=[('rebuild01'",start)
    s=s[:start]+s[end:]
    ast.parse(s);(W/'scripts/verify_probe_rebuild01.py').write_text(s,encoding='utf-8')
    s=(W/'scripts/summarize_navfocus.py').read_text(encoding='utf-8')
    s=s.replace('navfocus_final','rebuild01_final').replace('navfocus','rebuild01')
    s=s.replace("assert m['runtime_lock_sha256']==plan['runtime_lock_sha256']","assert m['runtime_lock_sha256']==sha(W/'protocol/rebuild01_final.json')")
    start=s.index("    f=W/'reports/rebuild01_records_verified.json'")
    end=s.index('    gate=bool(',start)
    s=s[:start]+'''    f=W/'reports/rebuild01_final_execution_verified.json';verified=False;execution=False
    if f.exists():
        proof=read(f);verified=proof['all_verified'] and proof['records']==len(rows)==42
        execution=verified and all(r['decoder_and_tracking_algebra_verified'] for r in proof['cases'])
    original=read(W/'results/all_trials_receipt.json')
    history=list(original['all_executed_cases'])
    for suite in ['rebuild01_dev','rebuild01_expanded']:
        for op in sorted((W/'runs'/suite).glob('*/outcome.json')):
            o=read(op);m=read(op.parent/'manifest.json')
            sp=op.parent/'record'/('search_score.json' if o['case']['kind']=='search' else 'physical_score.json')
            history.append(dict(suite=suite,case=o['case'],record=op.parent.relative_to(W).as_posix(),
                success=o['success'],error=o.get('error'),flight_started=o['flight_started'],
                checkpoint_sha256=m['checkpoint_sha256'],outcome_sha256=sha(op),manifest_sha256=sha(op.parent/'manifest.json'),
                score_path=sp.relative_to(W).as_posix(),score_sha256=sha(sp)))
    assert len(history)==405 and len({r['record'] for r in history})==405
'''+s[end:]
    s=s.replace("role='VLA selects the instructed person from RGB and generates approach/stop velocity; detection independently confirms discovery. Conventional control stabilizes velocity and attitude.'",
        "role='VLA selects the instructed person through RGB/text-conditioned velocity plans. A decoded plan endpoint is tracked using own odometry; detector only confirms discovery. Instantaneous raw VLA velocities are not directly executed.'")
    s=s.replace('Both models use the same new rebuild01 controller and English prompts.','Both models use the same plan decoder, own-odometry tracking controller and English prompts.')
    s=s.replace('Stationary phases override horizontal VLA requests with zero; approach phases execute bounded VLA horizontal requests.',
        'Approach velocity is computed by tracking the endpoint encoded in VLA action chunks, with captured/current own-state motion compensation. Do not describe it as raw VLA velocity execution.')
    ast.parse(s);(W/'scripts/summarize_rebuild01.py').write_text(s,encoding='utf-8')
    s=(W/'scripts/describe_navfocus_failures.py').read_text(encoding='utf-8').replace('navfocus_final','rebuild01_final').replace('navfocus','rebuild01')
    ast.parse(s);(W/'scripts/describe_rebuild01_failures.py').write_text(s,encoding='utf-8')
    s=(W/'scripts/trial_index_navfocus.py').read_text(encoding='utf-8').replace('NAVFOCUS','REBUILD01').replace('navfocus_final','rebuild01_final').replace('navfocus','rebuild01')
    ast.parse(s);(W/'scripts/trial_index_rebuild01.py').write_text(s,encoding='utf-8')
    print('Prepared final evidence aggregation and independent static arithmetic checks.')
if __name__=='__main__':main()
