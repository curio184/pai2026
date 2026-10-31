"""Preregister a diagnostic on already exposed images, not the untouched final round."""
import datetime
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan_path = W / 'protocol/train04_english_diagnostic_probe.json'
    script_path = W / 'scripts/run_train04_diagnostic_probe.py'
    assert not plan_path.exists() and not script_path.exists()
    source = W / 'scripts/run_english_transition_probe.py'
    text = source.read_text(encoding='utf-8')
    text = text.replace('english_transition_probe.json', 'train04_english_diagnostic_probe.json')
    text = text.replace("selected=json.loads((W/'protocol/selected_final.json').read_text());layouts=", "selected=probe['selected'];layouts=")
    text = text.replace("models={'v1.0':P/plan['training']['initial_checkpoint'],'v1.1':W/'models'/selected['candidate']/'final'}", "models={'v1.1':W/'models'/selected['candidate']/'final'}")
    text = text.replace("out=W/'probe_english_transition/outputs'", "out=W/'probe_train04_english_dev/outputs'")
    text = text.replace("rows=[]\nwith", "assert sha(Path(__file__))==probe['script_sha256']\nassert json.loads((W/'runs/stress_train04_en/summary.json').read_text())['completed']==16\nassert json.loads((W/'pipeline_train04_en_status.json').read_text())['stage']=='development_review'\nfor name,h in probe['image_sha256'].items():assert sha(W/name)==h\nrows=[]\nwith")
    text = text.replace("if not dest.exists():Image.open(src).convert('RGB').save(dest,quality=70)", "assert dest.exists(),'Diagnostic must reuse existing images without modification'")
    assert 'selected_final.json' not in text and 'probe_english_transition/outputs' not in text
    script_path.write_text(text, encoding='utf-8')
    original = json.loads((W / 'protocol/english_transition_probe.json').read_text())
    trained = json.loads((W / 'models/train04_en/result.json').read_text())
    original.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        purpose='Post-development diagnostic of completed train04_en on exposed round-1 views. Not final validation.',
        inference_gate='Only after all 16 preregistered stress cases finish and the pipeline stops for development review',
        models=['v1.1'], selected=dict(candidate='train04_en', checkpoint_sha256=trained['checkpoint_sha256']),
        flow_seed=20261024, planned_outputs=64, new_training=False, fresh_round02_access=False,
        original_probe_sha256=sha(W / 'protocol/english_transition_probe.json'),
        script_sha256=sha(script_path),
        baseline_reference='probe_english_transition/outputs/summary.json',
        baseline_reference_sha256=sha(W / 'probe_english_transition/outputs/summary.json'))
    original['image_sha256'] = {f"probe/images/{f['id']:05d}.jpg": sha(W / f"probe/images/{f['id']:05d}.jpg")
                                for f in original['frames']}
    plan_path.write_text(json.dumps(original, indent=2), encoding='utf-8')
    print(json.dumps(dict(protocol_sha256=sha(plan_path), script_sha256=sha(script_path),
                          images=len(original['frames']), planned_outputs=64, executed=False)))


if __name__ == '__main__':
    main()
