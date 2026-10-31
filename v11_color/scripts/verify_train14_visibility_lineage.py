"""Carry forward render-density evidence only after exact image-identity checks."""
import copy,datetime,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parent=W/'reports/v11_training_visibility_scope.json';old=read(parent)
assert old['verified'] and old['dataset']=='data/dataset13_en'
assert sha(W/'data/dataset13_en/audit.json')==old['dataset_audit_sha256']
data=W/'data/dataset14_en';audit=read(data/'audit.json')
assert audit['images_unchanged'] and audit['states_unchanged'] and audit['evaluation_images_or_states_used_for_training']==0
assert sha(data/'image_sources.json')==old['image_source_manifest_sha256']==sha(W/'data/dataset13_en/image_sources.json')
sources=read(data/'image_sources.json');assert len(sources)==old['images']==8408
for row in sources:assert sha(W/row['path'])==row['sha256'],row['id']
for row in old['render_manifests']:assert sha(W/row['path'])==row['sha256']
report=copy.deepcopy(old);report.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    dataset='data/dataset14_en',dataset_audit_sha256=sha(data/'audit.json'),
    parent_visibility_report='reports/v11_training_visibility_scope.json',parent_visibility_sha256=sha(parent),
    verification_method='All8408 current image hashes and the exact image-source manifest were checked. PNG-to-JPEG identity and density provenance are inherited transitively from the preserved parent audit for those same bytes; no new render or density claim.',
    current_training_image_hashes_rechecked=8408,
    inherited_render_checks_reexecuted=False,teacher_relabeling_changes_images=False)
dest=W/'reports/v11_training_visibility_train14.json';assert not dest.exists()
dest.write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(dict(path=str(dest),sha256=sha(dest),verified=True,images=len(sources))))
