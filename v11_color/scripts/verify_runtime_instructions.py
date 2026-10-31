"""Check actual English instructions and checkpoint identities in completed flights."""
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    allowed = {row[2] for row in read(W / 'data/dataset04_en/manifest.json')['prompt_variants']}
    cases = []
    for outcome_path in sorted((W / 'runs').glob('*/*/outcome.json')):
        folder = outcome_path.parent
        manifest = read(folder / 'manifest.json')
        if manifest.get('prompt_language') != 'English':
            continue
        outcome = read(outcome_path)
        path = folder / 'record/vla_link_events.json'
        if not path.exists():
            cases.append(dict(record=folder.relative_to(W).as_posix(), checked=False,
                              reason='No inference log; infrastructure failure retained',
                              outcome_error=outcome.get('error')))
            continue
        inferences = [r for r in read(path) if r['event'] == 'inference']
        instructions = sorted({r['instruction'] for r in inferences})
        checkpoints = sorted({r['checkpoint_sha256'] for r in inferences})
        assert inferences, str(path)
        assert set(instructions).issubset(allowed), instructions
        assert checkpoints == [manifest['checkpoint_sha256']], checkpoints
        cases.append(dict(record=folder.relative_to(W).as_posix(), checked=True,
                          flight_success=outcome['success'], inference_count=len(inferences),
                          instructions=instructions, checkpoints=checkpoints,
                          inference_log_sha256=sha(path)))
    proof = dict(completed_english_cases=len(cases), checked=sum(c['checked'] for c in cases),
                 all_completed_cases_checked=bool(cases) and all(c['checked'] for c in cases),
                 inference_count=sum(c.get('inference_count', 0) for c in cases),
                 cases=cases, allowed_instructions=sorted(allowed),
                 scope='Actual inference request logs, including failed completed flights; no new inference')
    output = W / 'reports/runtime_english_instructions_verified.json'
    output.write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in proof.items() if key not in ['cases', 'allowed_instructions']}))
    return proof


if __name__ == '__main__':
    main()
