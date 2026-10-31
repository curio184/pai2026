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
    parser.add_argument('--candidate',type=Path,default=W/'publication_candidate_rebuild03')
    parser.add_argument('--review-incomplete',action='store_true')
    a=parser.parse_args();root=a.candidate.resolve()
    assert root.is_dir()
    assert (root/'VERSION').read_text(encoding='utf-8').strip()==('1.1.0-review' if a.review_incomplete else '1.1.0')
    manifest=read(root/'DISTRIBUTION_MANIFEST.json')
    mismatches=[r['path'] for r in manifest['files'] if not (root/r['path']).is_file() or sha(root/r['path'])!=r['sha256']]
    assert not mismatches,mismatches
    # README is intentionally overlaid; its final provenance entry is authoritative.
    provenance={r['path']:r for r in read(root/'v11_color/PUBLICATION_PROVENANCE.json')['files']}
    assert all(sha(root/name)==r['distributed_sha256'] for name,r in provenance.items())
    broken=[];checked=0
    for relative in ['README.md','RELEASE_NOTES_v1.1.0.md','v11_color/ALL_TRIALS.md','v11_color/PUBLICATION_SCOPE.md','v11_color/prior/T5_source_index.md']:
        source=root/relative
        for target in re.findall(r'\]\(([^)]+)\)',source.read_text(encoding='utf-8')):
            target=target.strip('<>').split('#')[0]
            if not target or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',target):continue
            dest=(source.parent/unquote(target)).resolve();checked+=1
            if not dest.is_relative_to(root) or not dest.exists():broken.append(dict(source=relative,target=target))
    assert not broken,broken
    result=read(root/'v11_color/results/all_trials_rebuild03.json')
    assert result['preregistered_goal_met']
    assert result['completed']==42 and result['all_new_records_independently_rescored'] and result['probe_arithmetic_and_images_verified']
    original_verification=read(root/'v11_color/results/REPLAY_VERIFICATION.json')
    expected=sum(bool(r.get('score_path')) for r in result['all_executed_cases'])
    assert expected==454 and original_verification['records']==42
    assert read(root/'v11_color/reports/train15_en_all_records_verified.json')['records']==287
    assert read(root/'v11_color/reports/control_v11_records_verified.json')['records']==8
    for row in result['all_executed_cases']:
        assert (root/'v11_color'/row['record']/'outcome.json').is_file()
        if row.get('score_path'):
            score=read(root/'v11_color'/row['score_path'])
            assert score['success']==row['success']
    logs=W/'reports/publication_rebuild03_checks';logs.mkdir(exist_ok=True)
    for name,script in [('v1_original','verify.py'),('v11_final','v11_color/scripts/verify_rebuild03.py'),('intervention_metrics','v11_color/scripts/verify_probe_rebuild03.py'),('v10_teacher_reference','v11_color/scripts/verify_v10_teacher_reference.py'),('v10_language_reference','v11_color/scripts/verify_v10_language_reference.py')]:
        command=[sys.executable,str(root/script)]
        if name!='v1_original':command.append('--no-write')
        with (logs/(name+'.log')).open('w',encoding='utf-8') as output:
            completed=subprocess.run(command,cwd=root,stdout=output,stderr=subprocess.STDOUT)
        assert completed.returncode==0,('Review replay failed; inspect log',name)
    assert all(sha(root/r['path'])==r['sha256'] for r in manifest['files']), 'Verification changed distribution files'
    report=dict(candidate=str(root),manifest_files=len(manifest['files']),local_links_checked=checked,
                additional_records=expected,original_five_records_verified=True,
                final_42_replayed_from_distribution=True,historical_295_local_replays_preserved=True,provenance_verified=True,
                goal_met=result['preregistered_goal_met'],review_only=a.review_incomplete,published=False,tagged=False,submitted=False)
    (W/'reports/publication_rebuild03_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
