"""Clarify the main command flow and separately explain detector support."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
from pypdf import PdfReader, PdfWriter

BASE = Path(__file__).resolve().parents[1]
PROJECT = BASE.parent
sys.path.insert(0, str(BASE / 'scripts'))
source = BASE / 'reports/wording03/build_report_wording03_generated.py'
original = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し03.pdf'
output = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し04.pdf'
work = BASE / 'reports/wording04'
work.mkdir(parents=True, exist_ok=True)
old_hash = hashlib.sha256(original.read_bytes()).hexdigest()
text = source.read_text(encoding='utf-8')
old = "p('任務管理プログラムが、離陸から捜索、着陸までの手順を管理する。検出器が対象者の発見を確認すると、SmolVLAに「青い服の人に近づいて止まって」などと指示する。',9.2,gap=5)"
new = "p('任務管理プログラムが、離陸から捜索、着陸までの手順を管理し、各工程の完了を判断する。接近の工程では、任務管理プログラムがSmolVLAに「青い服の人に近づいて止まって」などと指示する。',9.2,gap=5)"
assert text.count(old) == 1
text = text.replace(old, new)
old = "('任務管理プログラム','離陸から着陸までの工程を管理し、VLAへの指示や、次の工程へ進むタイミングを決める。')"
new = "('任務管理プログラム','機体の状態や検出器の情報をもとに各工程の完了を判断し、次の工程への切り替えとVLAへの指示を行う。')"
assert text.count(old) == 1
text = text.replace(old, new)
old = "('SSDlite＋色判定','指定した色の服を着た人を連続3画像で確認する。接近中も対象者が見えているかを調べ、工程を切り替える判断を支援する。')"
new = "('SSDlite＋色判定','指定した色の服を着た人を連続3画像で確認し、結果を任務管理に伝える。接近中も対象者が見えているかを確認する。')"
assert text.count(old) == 1
text = text.replace(old, new)
old = "p('接近中に対象者を見失った場合は、検出器の情報をもとに任務管理が再捜索や着陸に切り替える。離陸・見回しの旋回・着陸は通常の制御で実行する。',8.8)"
new = "p('工程の区切りを判断するために、検出器を併用する。任務管理プログラムは、検出器が確認した対象者の発見や見失いを、工程を切り替える判断に使う。接近中に対象者を見失った場合は、再捜索や着陸に切り替える。離陸・見回しの旋回・着陸は通常の制御で実行する。',8.8)"
assert text.count(old) == 1
text = text.replace(old, new)
text = text.replace('文言見直し03_全頁生成.pdf', '文言見直し04_全頁生成.pdf')
text = text.replace('reports/wording03/generated_', 'reports/wording04/generated_')
generated_source = work / 'build_report_wording04_generated.py'
generated_source.write_text(text, encoding='utf-8')
scope = {'__file__': str(BASE / 'scripts/build_report_rebuild03.py'), '__name__': '__main__'}
exec(compile(text, str(generated_source), 'exec'), scope)

old_reader = PdfReader(original)
generated_reader = PdfReader(scope['OUT'])
assert len(old_reader.pages) == len(generated_reader.pages) == 4
writer = PdfWriter()
writer.add_page(generated_reader.pages[0])
for page in old_reader.pages[1:]:
    writer.add_page(page)
writer.add_metadata({'/Title': '災害救助ドローン / v1.1 検証更新版', '/Subject': 'Physical AI 応用1 最終課題'})
with output.open('wb') as f:
    writer.write(f)
final = PdfReader(output)
first = final.pages[0].extract_text()
compact = ''.join(first.split())
for phrase in ['各工程の完了を判断する。', '接近の工程では、任務管理プログラムがSmolVLAに', '工程の区切りを判断するために、検出器を併用する。', '結果を任務管理に伝える。', '物理：MuJoCo', '描画：Blender', '限られた人手']:
    assert ''.join(phrase.split()) in compact, phrase
assert '検出器が対象者の発見を確認すると' not in compact
table_text = first.split('担当\n役割', 1)[1]
order = ['任務管理プログラム', 'SSDlite＋色判定', 'SmolVLA', '実行部', 'ArduPilot']
indices = [table_text.index(item) for item in order]
assert indices == sorted(indices)
for i in range(1, 4):
    assert final.pages[i].extract_text() == old_reader.pages[i].extract_text()
    assert final.pages[i].get_contents().get_data() == old_reader.pages[i].get_contents().get_data()
assert hashlib.sha256(original.read_bytes()).hexdigest() == old_hash
receipt = dict(output=str(output), pages=4, sha256=hashlib.sha256(output.read_bytes()).hexdigest(), source_sha256=old_hash, source_unchanged=True, pages_2_to_4_content_streams_unchanged=True, visually_reviewed=False, created_utc=datetime.now(timezone.utc).isoformat(), editorial_flow='Mission judgement -> explicit instruction to VLA -> generated movement -> execution. Detector support explained separately.')
(work / 'check.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(output)
