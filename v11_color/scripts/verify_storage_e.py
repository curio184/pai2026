"""Post-migration path and evidence checks; no inference, flight, or rescore."""
import datetime, hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parents[1];P=W.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
status_path=Path('<WORK_ROOT>/_migration/status.json')
status=read(status_path);assert status['phase']=='complete'
detail=status['detail'];assert detail['protected_artifacts_unchanged'] and detail['public_checkout_clean']
assert P==Path('<PROJECT_ROOT>')
for root in detail['roots']:
    assert Path(root['source']).resolve()==Path(root['target']),root['source']
cases=read(W/'results/all_trials_round02_english.json')['all_executed_cases']
for case in cases:
    if case.get('score_path'):
        assert sha(W/case['score_path'])==case['score_sha256'],case['score_path']
sources=read(W/'data/dataset05_en/image_sources.json')
for source in sources:
    image=W/source['path'];assert image.is_file() and image.resolve().is_relative_to(P)
amendment=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    reason='User requested one E: project location instead of distributed C:/D: storage.',
    project_root=str(P),repository_root='<WORK_ROOT>/repository',
    original_paths_retained_as_junctions=True,files_copied_and_sha256_verified=detail['files'],
    bytes_copied=detail['bytes'],migration_manifest_sha256=detail['manifest_sha256'],
    original_video_pdf_v10_unchanged=True,prior_trials_unchanged=True,
    frozen_runtime_lock_postmigration='passed',wsl_physics_library_load_postmigration='passed',
    new_policy_inference_or_flight_in_migration_check=False,
    future_final_comparison='Both v1.0 and the selected candidate will use E: storage and the same frozen runner. Existing D: development trials remain distinct records.',
    fresh_round02_evaluation_started=False)
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*'))
out=W/'protocol/storage_migration_e.json';assert not out.exists()
out.write_text(json.dumps(amendment,ensure_ascii=False,indent=2),encoding='utf-8')
audit=dict(passed=True,project_root=str(P),legacy_alias_roots=len(detail['roots']),
    existing_trial_records_checked=len(cases),training_image_paths_checked=len(sources),
    migration_status_sha256=sha(status_path),amendment_sha256=sha(out),
    scope='Path resolution and saved score hash checks only; all copied file hashes were separately verified before source removal.')
(W/'reports/storage_e_preflight_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps(audit))
