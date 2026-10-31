from pathlib import Path
W=Path(__file__).resolve().parents[1]
s=(W/'scripts/audit_rebuild03_execution.py').read_text(encoding='utf-8')
first=s.index('    from run_suite_rebuild03 import P,OLD_BUILD')
last=s.index('    tempbase=',first)
s=s[:first]+"    from verify_records_round02_english import scene_path\n    scene=scene_path(case)\n    assert expected_hash(scene,manifest['physics_sha256'])\n"+s[last:]
s=s[:s.index('def main():')]
s+='''def expected_hash(path,digest):
    actual=sha(path)
    if actual==digest:return True
    provenance=W/'PUBLICATION_PROVENANCE.json'
    if not provenance.exists():return False
    rel=path.relative_to(W.parent).as_posix()
    return any(r['path']==rel and r['original_sha256']==digest and r['distributed_sha256']==actual and r['path_redaction_only'] for r in read(provenance)['files'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--no-write',action='store_true');a=p.parse_args()
    plan=read(W/'protocol/rebuild03_final.json');rows=[]
    for case in plan['cases']:
        folder=W/'runs/rebuild03_final'/(case['id']+'_'+case['model'])
        manifest=read(folder/'manifest.json');outcome=read(folder/'outcome.json')
        assert manifest['case']==outcome['case']==case
        assert expected_hash(W/'protocol/rebuild03_final.json',manifest['final_protocol_sha256'])
        assert expected_hash(W/'scripts/run_suite_rebuild03_final.py',manifest['runner_script_sha256'])
        assert manifest['checkpoint_sha256']==plan['checkpoint_sha256' if case['model']=='v1.1' else 'old_checkpoint_sha256']
        row=verify(folder);rows.append(row);print(json.dumps(row),flush=True)
    assert len(rows)==42
    result=dict(records=42,all_verified=True,complete=True,cases=rows)
    if not a.no_write:(W/'reports/portable_rebuild03_verified.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=42,all_verified=True)))
if __name__=='__main__':main()
'''
(W/'scripts/verify_rebuild03.py').write_text(s,encoding='utf-8')
