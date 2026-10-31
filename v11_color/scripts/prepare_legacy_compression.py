"""Prepare an exact-file compression plan for four inactive pre-submission candidates."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
source=(W/'scripts/compress_archived_models_e.py').read_text(encoding='utf8')
source=source.replace("W=Path(__file__).resolve().parents[1]", "W=Path(__file__).resolve().parents[1];P=W.parent")
source=source.replace('ntfs_archive_compression.json','ntfs_legacy_model_compression.json')
old="ARCHIVES=['train01','train02','train03','train04_en','train05_en','train06_en','train07_en','train08_en','train09_en']"
new="ARCHIVES=['smolvla_training','smolvla_training_civic_01','smolvla_training_realism_01','smolvla_training_revision_02']"
assert old in source;source=source.replace(old,new)
source=source.replace("for rel in ['final/model.safetensors','recovery.pt']:", "for rel in ['final/model.safetensors']:")
old="expected=read(W/'models'/candidate/'result.json')['checkpoint_sha256'] if rel.startswith('final/') else None"
assert old in source;source=source.replace(old,"expected=None  # Record full SHA-256 immediately before and after compression.")
source=source.replace("W/'models'", "P/'outputs'").replace('p.relative_to(W)','p.relative_to(P)').replace("contained(W/item['path'])","contained(P/item['path'])")
source=source.replace("target_free_gib=10", "target_free_gib=8")
source=source.replace("reports/archive_compression", "reports/legacy_model_compression")
source=source.replace('inactive candidates','inactive pre-submission candidates')
assert "W/'models'" not in source and 'smolvla_training_realism_precision_02' not in source
ast.parse(source);out=W/'scripts/compress_legacy_models_e.py';assert not out.exists();out.write_text(source,encoding='utf8')
print('Prepared four-file legacy compression script; protected submitted v1.0 excluded.')
