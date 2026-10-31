"""Read-only checks of the submitted artifacts and the English runtime amendment."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

W = Path(__file__).resolve().parents[1]
P = W.parent


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    protected = {
        'outputs/smolvla_training_realism_precision_02/final/model.safetensors':
            'd119adc57fa0c4681f4413b621d6321d27b000c6a3550c5b075bbbebc3d9a467',
        'output/video/rescue_drone_final_quad.mp4':
            '9669ae47300089f327ac347f9e07efcd6c9e02c05cb7ef91212f779af404ed51',
        'output/pdf/説明資料_PAI最終課題_最終版.pdf':
            '7bf86e3ab13bc47b0a0f994698bc0d0c1d920648facbacf7ba5f9e16d4c80119',
    }
    checks = []
    for name, expected in protected.items():
        actual = sha(P / name)
        checks.append(dict(path=name, expected_sha256=expected,
                           actual_sha256=actual, unchanged=actual == expected))
    lock = read(W / 'protocol/runtime_english_lock.json')
    runtime_checks = [dict(path=name, unchanged=sha(W / 'runtime_english' / name) == expected)
                      for name, expected in lock['runtime'].items()]
    import_checks = [dict(path=name, unchanged=sha(P / name) == expected)
                     for name, expected in lock['project_imports'].items()]
    manifest = read(W / 'data/dataset04_en/manifest.json')
    substitutions = [(variants[2].encode(), variants[0].encode())
                     for variants in manifest['prompt_variants']]
    changes = []
    for path in sorted((W / 'runtime_english').rglob('*.py')):
        relative = path.relative_to(W / 'runtime_english')
        original = W / 'runtime' / relative
        if not original.exists() or path.read_bytes() == original.read_bytes():
            continue
        restored = path.read_bytes()
        for english, bilingual in substitutions:
            restored = restored.replace(b'"' + english + b'"', b'"' + bilingual + b'"')
        changes.append(dict(path=relative.as_posix(),
                            original_reconstructed=restored == original.read_bytes()))
    checkout = Path('C:/Temp/pai2026_submission/pai2026')
    status = subprocess.run(['git', '-C', str(checkout), 'status', '--porcelain'],
                            capture_output=True, text=True, check=True).stdout
    head = subprocess.run(['git', '-C', str(checkout), 'rev-parse', 'HEAD'],
                          capture_output=True, text=True, check=True).stdout.strip()
    result = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  protected_artifacts=checks, runtime_files=runtime_checks,
                  project_imports=import_checks, instruction_only_changes=changes,
                  local_public_checkout_clean=not status.strip(), public_checkout_head=head,
                  scope='Local read-only checks; no remote mutation or flight evaluation')
    result['passed'] = (all(c['unchanged'] for c in checks + runtime_checks + import_checks)
                        and {c['path'] for c in changes} == set(lock['changed_files'])
                        and all(c['original_reconstructed'] for c in changes)
                        and not status.strip()
                        and head == 'a4e5f01b51591b9cd32c5bc7cc3cde2d818fe83a')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = W / 'reports' / ('preservation_audit_' + stamp + '.json')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=result['passed'], report=str(output),
                          protected_artifacts=len(checks), runtime_files=len(runtime_checks),
                          imports=len(import_checks)), ensure_ascii=False))
    if not result['passed']:
        raise RuntimeError('Preservation audit failed; inspect the saved report')


if __name__ == '__main__':
    main()
