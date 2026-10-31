"""Distinguish the user's request from the mission program's VLA instructions."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
from pypdf import PdfReader, PdfWriter

BASE = Path(__file__).resolve().parents[1]
PROJECT = BASE.parent
sys.path.insert(0, str(BASE / 'scripts'))
source = BASE / 'reports/wording06/build_report_wording06_generated.py'
original = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し06.pdf'
output = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し07.pdf'
work = BASE / 'reports/wording07'
work.mkdir(parents=True, exist_ok=True)
source_hash = hashlib.sha256(original.read_bytes()).hexdigest()
text = source.read_text(encoding='utf-8')
old = '離陸・旋回・着陸は通常の制御で実行する。VLAには、現在の画像・機体状態と「Approach the person wearing blue and stop.」などの英語の工程指示を渡す。上位の「青い服の人を探して」は直接入力しない。人物の正解座標や検出枠は、VLAと実行部には渡さない。'
new = '利用者の「青い服の人を探して」という指示は、任務管理プログラムが受け付ける。VLAには「青い服の人に近づいて止まって」などの工程ごとの指示を英語で渡し、現在の画像・機体状態とともに入力する。離陸・旋回・着陸は通常の制御で実行する。人物の正解座標や検出枠は、VLAと実行部には渡さない。'
assert text.count(old) == 1
text = text.replace(old, new)
text = text.replace('文言見直し06_全頁生成.pdf', '文言見直し07_全頁生成.pdf')
text = text.replace('reports/wording06/generated_', 'reports/wording07/generated_')
generated_source = work / 'build_report_wording07_generated.py'
generated_source.write_text(text, encoding='utf-8')
scope = {'__file__': str(BASE / 'scripts/build_report_rebuild03.py'), '__name__': '__main__'}
exec(compile(text, str(generated_source), 'exec'), scope)

old_reader = PdfReader(original)
generated = PdfReader(scope['OUT'])
assert len(old_reader.pages) == len(generated.pages) == 4
writer = PdfWriter()
writer.add_page(generated.pages[0])
for page in old_reader.pages[1:]:
    writer.add_page(page)
writer.add_metadata({'/Title': '災害救助ドローン / v1.1 検証更新版', '/Subject': 'Physical AI 応用1 最終課題'})
with output.open('wb') as f:
    writer.write(f)
final = PdfReader(output)
compact = ''.join(final.pages[0].extract_text().split())
assert ''.join(new.split()) in compact
assert '上位の' not in compact
for i in range(1, 4):
    assert final.pages[i].extract_text() == old_reader.pages[i].extract_text()
    assert final.pages[i].get_contents().get_data() == old_reader.pages[i].get_contents().get_data()
assert hashlib.sha256(original.read_bytes()).hexdigest() == source_hash
receipt = dict(output=str(output), pages=4, sha256=hashlib.sha256(output.read_bytes()).hexdigest(), source_sha256=source_hash, source_unchanged=True, pages_2_to_4_content_streams_unchanged=True, visually_reviewed=False, created_utc=datetime.now(timezone.utc).isoformat(), change='Explicit user -> mission management -> English stage instruction -> VLA relationship; preserve concise section and role order.')
(work / 'check.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(output)
