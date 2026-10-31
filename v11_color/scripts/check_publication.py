"""Validate the assembled review copy without changing the live checkout."""
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import unquote

W=Path(__file__).resolve().parents[1]

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate',type=Path,default=W/'publication_candidate')
    a=parser.parse_args();root=a.candidate.resolve()
    assert root.is_dir()
    manifest=read(root/'DISTRIBUTION_MANIFEST.json')
    mismatches=[r['path'] for r in manifest['files'] if not (root/r['path']).is_file() or sha(root/r['path'])!=r['sha256']]
    assert not mismatches,mismatches
    # README is intentionally overlaid; its final provenance entry is authoritative.
    provenance={r['path']:r for r in read(root/'v11_color/PUBLICATION_PROVENANCE.json')['files']}
    assert all(sha(root/name)==r['distributed_sha256'] for name,r in provenance.items())
    broken=[];checked=0
    for relative in ['README.md','v11_color/ALL_TRIALS.md','v11_color/PUBLICATION_SCOPE.md']:
        source=root/relative
        for target in re.findall(r'\]\(([^)]+)\)',source.read_text(encoding='utf-8')):
            target=target.strip('<>').split('#')[0]
            if not target or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',target):continue
            dest=(source.parent/unquote(target)).resolve();checked+=1
            if not dest.is_relative_to(root) or not dest.exists():broken.append(dict(source=relative,target=target))
    assert not broken,broken
    result=read(root/'v11_color/results/all_trials.json')
    assert result['preregistered_goal_met']
    original_verification=read(root/'v11_color/results/REPLAY_VERIFICATION.json')
    expected=sum(bool(r.get('score_path')) for r in result['all_executed_cases'])
    assert expected==original_verification['records']
    for row in result['all_executed_cases']:
        assert (root/'v11_color'/row['record']/'outcome.json').is_file()
        if row.get('score_path'):
            score=read(root/'v11_color'/row['score_path'])
            assert score['success']==row['success']
    logs=W/'reports/publication_checks';logs.mkdir(exist_ok=True)
    for name,script in [('v1_original','verify.py'),('v11_all','v11_color/scripts/verify_records.py')]:
        command=[sys.executable,str(root/script)]
        with (logs/(name+'.log')).open('w',encoding='utf-8') as output:
            completed=subprocess.run(command,cwd=root,stdout=output,stderr=subprocess.STDOUT)
        assert completed.returncode==0,('Review replay failed; inspect log',name)
    report=dict(candidate=str(root),manifest_files=len(manifest['files']),local_links_checked=checked,
                additional_records=expected,original_five_records_verified=True,
                all_additional_records_verified=True,provenance_verified=True,
                published=False,tagged=False,submitted=False)
    (W/'reports/publication_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
