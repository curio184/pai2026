"""Register a small language-scope check; no rendering or inference is run here."""
import datetime
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))

plan = read(W/'protocol/static_probe_rebuild03.json')
plan.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    purpose='Retain all original English results. Check the original v1.0 bilingual instruction on exactly the same32 reserved images; no changes to final acceptance.',
    models=['v1.0'], prompts={'original_bilingual':read(W/'data/dataset04_en/manifest.json')['prompts'][:2]},
    original_english_protocol_sha256=sha(W/'protocol/static_probe_rebuild03.json'),
    image_source='probe_rebuild03/images',
    acceptance='Reference only. Report all64 outputs, regardless of outcome. Original gate is unchanged.')
destination = W/'protocol/v10_language_reference.json'
assert not destination.exists()
destination.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')

source=(W/'scripts/run_probe_rebuild03.py').read_text(encoding='utf-8')
source=source.replace('protocol/static_probe_rebuild03.json','protocol/v10_language_reference.json')
source=source.replace("models={'v1.0':P/plan['training']['initial_checkpoint'],'v1.1':W/'models'/selected['candidate']/'final'}", "models={'v1.0':P/plan['training']['initial_checkpoint']}")
source=source.replace("out=W/'probe_rebuild03/outputs'", "out=W/'probe_v10_language/outputs'")
source=source.replace("out=W/'probe_v10_language/outputs';", "receipt=json.loads((W/'protocol/v10_language_reference_execution.json').read_text());assert receipt['protocol_sha256']==sha(W/'protocol/v10_language_reference.json') and receipt['runner_sha256']==sha(Path(__file__))\nout=W/'probe_v10_language/outputs';")
runner=W/'scripts/run_v10_language_reference.py'
runner.write_text(source,encoding='utf-8')

source=(W/'scripts/verify_probe_rebuild03.py').read_text(encoding='utf-8')
source=source.replace("('rebuild03','probe_rebuild03','probe_rebuild03/images','static_probe_rebuild03.json'", "('v10_language','probe_v10_language','probe_rebuild03/images','v10_language_reference.json'")
source=source.replace("if selection is None:expected_hashes=", "expected_hashes=")
source=source.replace('reports/probe_rebuild03_verified.json','reports/v10_language_reference_verified.json')
verifier=W/'scripts/verify_v10_language_reference.py'
verifier.write_text(source,encoding='utf-8')
receipt=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    protocol_sha256=sha(destination),runner_sha256=sha(runner),verifier_sha256=sha(verifier),
    outputs=64,flight_count=0,models=['v1.0'],num_steps=5,
    gpu_scheduling='Run only after all42 original cases and all16 teacher-compatible reference cases have ended.')
(W/'protocol/v10_language_reference_execution.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt))
