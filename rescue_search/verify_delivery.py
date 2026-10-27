"""Validate the delivered archive in a fresh directory, without cached scores."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

root = Path(os.environ['RESCUE_PROJECT_ROOT'])
here = Path(__file__).resolve().parent
dest = root / 'output/video/presentation_v3'
delivery = json.loads((dest / 'delivery.json').read_text(encoding='utf8'))
for name in ['video', 'pdf', 'code']:
    actual = hashlib.sha256(Path(delivery[name]).read_bytes()).hexdigest()
    assert actual == delivery[name + '_sha256'], name

replay = here / 'archive_replay'
replay.mkdir(exist_ok=False)
skipped = []
with zipfile.ZipFile(delivery['code']) as z:
    assert z.testzip() is None
    for entry in z.infolist():
        target = (replay / entry.filename).resolve()
        assert target.is_relative_to(replay.resolve()), entry.filename
        if Path(entry.filename).name in ['physical_score.json', 'search_score.json', 'audit.json']:
            skipped.append(entry.filename)
            continue
        z.extract(entry, replay)
extracted = replay / 'rescue-drone-vla'
env = dict(os.environ, RESCUE_PROJECT_ROOT=str(extracted), PYTHONUTF8='1')
completed = subprocess.run([sys.executable, 'rescue_search/audit_run.py', 'eval03'],
                           cwd=extracted, env=env, capture_output=True, text=True, encoding='utf8')
(dest / 'archive_replay.log').write_text(completed.stdout + completed.stderr, encoding='utf8')
assert completed.returncode == 0, completed.stderr
fresh = json.loads((extracted / 'rescue_search/runs/eval03/audit.json').read_text(encoding='utf8'))
original = json.loads((here / 'runs/eval03/audit.json').read_text(encoding='utf8'))
assert fresh['success'] and len(fresh['cases']) == 4
assert fresh == original, 'Fresh independent scores differ from original audit'
report = dict(success=True, archive_sha256=delivery['code_sha256'],
              fresh_physical_scoring=True, cached_scores_excluded=skipped,
              exactly_matches_original_audit=True,
              cases=[dict(condition=c['condition'], success=c['success'],
                          camera_frame_count=c['camera_frame_count']) for c in fresh['cases']],
              extracted_directory=str(extracted), archive_crc_valid=True,
              video_pdf_code_hashes_verified=True)
(dest / 'archive_replay.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
meta_path = root / 'output/video/rescue_drone_presentation_v3.json'
meta = json.loads(meta_path.read_text(encoding='utf8'))
meta['goal_complete_pending_final_archive_replay'] = False
meta['archive_replay'] = str(dest / 'archive_replay.json')
meta['local_deliverables_complete'] = True
meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(dict(success=True, cases=report['cases'], exactly_matches_original_audit=True)))
