"""One message, one role table, and concise implementation boundaries."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
from pypdf import PdfReader, PdfWriter

BASE = Path(__file__).resolve().parents[1]
PROJECT = BASE.parent
sys.path.insert(0, str(BASE / 'scripts'))
source = BASE / 'reports/wording05/build_report_wording05_generated.py'
original = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し05.pdf'
output = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し06.pdf'
work = BASE / 'reports/wording06'
work.mkdir(parents=True, exist_ok=True)
source_hash = hashlib.sha256(original.read_bytes()).hexdigest()
text = source.read_text(encoding='utf-8')
start = text.index("label('自律飛行を支える役割分担')")
end = text.index("start('IMPLEMENTATION'", start)
section = '''label('自律飛行を支える役割分担')
p('任務管理が捜索の手順を進め、SmolVLAが対象者に近づいて止まる動作を決める。',9.2)
table(['担当','役割'],[
 ('任務管理プログラム','各工程の完了を判断して次へ進め、SmolVLAへの指示を切り替える。'),
 ('SmolVLA','画像・指示・機体状態から、指定された人物への接近・減速・停止の動作列を生成する。'),
 ('実行部','撮影後の機体の移動を補正し、VLAの計画を飛行指令に変換する。'),
 ('ArduPilot','モーターを制御し、機体の姿勢を安定させる。'),
 ('SSDlite＋色判定','対象者が見えているかを任務管理に伝え、工程の切り替えの判断を支援する。発見は連続3画像で確認する。')],[108,CW-108],size=8.7)
p('離陸・旋回・着陸は通常の制御で実行する。VLAには、現在の画像・機体状態と「Approach the person wearing blue and stop.」などの英語の工程指示を渡す。上位の「青い服の人を探して」は直接入力しない。人物の正解座標や検出枠は、VLAと実行部には渡さない。',8.5,color=GRAY,gap=0)

'''
old_section = text[start:end]
text = text[:start] + section + text[end:]
text = text.replace('文言見直し05_全頁生成.pdf', '文言見直し06_全頁生成.pdf')
text = text.replace('reports/wording05/generated_', 'reports/wording06/generated_')
generated_source = work / 'build_report_wording06_generated.py'
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
first = final.pages[0].extract_text()
compact = ''.join(first.split())
table_text = first.split('担当\n役割', 1)[1]
order = ['任務管理プログラム', 'SmolVLA', '実行部', 'ArduPilot', 'SSDlite＋色判定']
indices = [table_text.index(s) for s in order]
assert indices == sorted(indices)
for phrase in ['任務管理が捜索の手順を進め、SmolVLAが対象者に近づいて止まる動作を決める。', '工程の切り替えの判断を支援する。', '上位の「青い服の人を探して」は直接入力しない。', '連続3画像', '物理：MuJoCo', '描画：Blender', '限られた人手']:
    assert ''.join(phrase.split()) in compact, phrase
for i in range(1, 4):
    assert final.pages[i].extract_text() == old_reader.pages[i].extract_text()
    assert final.pages[i].get_contents().get_data() == old_reader.pages[i].get_contents().get_data()
assert hashlib.sha256(original.read_bytes()).hexdigest() == source_hash
receipt = dict(output=str(output), pages=4, sha256=hashlib.sha256(output.read_bytes()).hexdigest(), source_sha256=source_hash, source_unchanged=True, pages_2_to_4_content_streams_unchanged=True, visually_reviewed=False, created_utc=datetime.now(timezone.utc).isoformat(), message='Mission management advances the task; SmolVLA determines approach and stopping motions.', role_order=order, old_section_source_chars=len(old_section), new_section_source_chars=len(section))
(work / 'check.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(output)
