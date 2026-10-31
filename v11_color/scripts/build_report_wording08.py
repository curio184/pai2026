"""Remove submission/version wording from the footer on all four pages."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
from pypdf import PdfReader, PdfWriter

BASE = Path(__file__).resolve().parents[1]
PROJECT = BASE.parent
sys.path.insert(0, str(BASE / 'scripts'))
source = BASE / 'reports/wording07/build_report_wording07_generated.py'
original = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し07.pdf'
output = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し08.pdf'
work = BASE / 'reports/wording08'
work.mkdir(parents=True, exist_ok=True)
source_hash = hashlib.sha256(original.read_bytes()).hexdigest()
text = source.read_text(encoding='utf-8')
old = "c.drawString(L,22,'Physical AI 応用1 / 最終課題・v1.1 '+('検証レビュー（合格条件未達）' if review else '検証更新版'))"
new = "c.drawString(L,22,'Physical AI 応用1')"
assert text.count(old) == 1
text = text.replace(old, new)
text = text.replace('文言見直し07_全頁生成.pdf', '文言見直し08_全頁生成.pdf')
text = text.replace('reports/wording07/generated_', 'reports/wording08/generated_')
generated_source = work / 'build_report_wording08_generated.py'
generated_source.write_text(text, encoding='utf-8')
scope = {'__file__': str(BASE / 'scripts/build_report_rebuild03.py'), '__name__': '__main__'}
exec(compile(text, str(generated_source), 'exec'), scope)

old_reader = PdfReader(original)
generated = PdfReader(scope['OUT'])
assert len(old_reader.pages) == len(generated.pages) == 4
writer = PdfWriter()
for page in generated.pages:
    writer.add_page(page)
writer.add_metadata({'/Title': '災害救助ドローン', '/Subject': 'Physical AI 応用1'})
with output.open('wb') as f:
    writer.write(f)
final = PdfReader(output)
removed = 'Physical AI 応用1 / 最終課題・v1.1 検証更新版'
for before, after in zip(old_reader.pages, final.pages):
    expected = ''.join(before.extract_text().replace(removed, 'Physical AI 応用1').split())
    actual = ''.join(after.extract_text().split())
    assert actual == expected
    assert '最終課題・v1.1 検証更新版' not in after.extract_text()
assert hashlib.sha256(original.read_bytes()).hexdigest() == source_hash
receipt = dict(output=str(output), pages=4, sha256=hashlib.sha256(output.read_bytes()).hexdigest(), source_sha256=source_hash, source_unchanged=True, text_changes_limited_to_footer=True, visually_reviewed=False, created_utc=datetime.now(timezone.utc).isoformat())
(work / 'check.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(output)
