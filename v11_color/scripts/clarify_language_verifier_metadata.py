"""Clarify the checkpoint named by the auxiliary verifier before its first run."""
import datetime,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
assert not (W/'probe_v10_language/outputs').exists(), 'This amendment must precede inference'
receipt=W/'protocol/v10_language_reference_execution.json'
original=json.loads(receipt.read_text(encoding='utf-8'))
source=W/'scripts/verify_v10_language_reference.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()==original['verifier_sha256']
archive=W/'protocol/v10_language_reference_execution_initial.json'
assert not archive.exists()
shutil.copy2(receipt,archive)
shutil.copy2(source,W/'scripts/verify_v10_language_reference_registered_initial.py')
text=source.read_text(encoding='utf-8').replace("selected_checkpoint_sha256=chosen['checkpoint_sha256']", "tested_checkpoint_sha256=expected_hashes['v1.0']")
source.write_text(text,encoding='utf-8')
original.update(amended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    amendment='Verifier report names the tested v1.0 checkpoint instead of the main v1.1 selection. No cases, images, prompts, noise, model, inference or metric changes. Before first inference.',
    verifier_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
receipt.write_text(json.dumps(original,indent=2),encoding='utf-8')
print('Auxiliary verifier checkpoint metadata clarified before execution.')
