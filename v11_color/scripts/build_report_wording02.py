"""Clarify whole-system roles, foregrounding SmolVLA; preserve other pages."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
from pypdf import PdfReader, PdfWriter

BASE = Path(__file__).resolve().parents[1]
PROJECT = BASE.parent
sys.path.insert(0, str(BASE / 'scripts'))
source = BASE / 'reports/wording01/build_report_wording01_generated.py'
original = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し01.pdf'
output = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し02.pdf'
work = BASE / 'reports/wording02'
work.mkdir(parents=True, exist_ok=True)
old_hash = hashlib.sha256(original.read_bytes()).hexdigest()
text = source.read_text(encoding='utf-8')

start = text.index("label('VLAが人を認識し、近づき、止まる')")
end = text.index("start('IMPLEMENTATION'", start)
section = '''label('自律飛行を支える役割分担')
p('飛行動作の生成を担うのが、SmolVLAである。カメラ映像と言葉による指示から、指定された人物への接近・減速・停止の動作を生成する。任務管理や検出器、飛行制御がそれを支え、離陸から捜索、着陸までの一連の動作を実現する。',9.2)
table(['担当','役割'],[
 ('SmolVLA','映像と指示から、指定された人物への移動方向・速度・減速・停止の動作を生成する。'),
 ('任務管理プログラム','離陸から着陸までの工程を管理し、VLAへの指示や、次の工程へ進むタイミングを決める。'),
 ('SSDlite＋色判定','指定した色の服を着た人を連続3画像で確認する。接近中も対象者が見えているかを調べ、工程を切り替える判断を支援する。'),
 ('実行部','撮影後に機体が動いた分を補正し、VLAが生成した計画に沿って飛行指令を出す。'),
 ('ArduPilot','飛行指令に応じてモーターを調整し、機体の姿勢を安定させる。')],[108,CW-108],size=8.7)
p('対象者が見つかると、任務管理がVLAに「青い服の人に近づいて止まって」などと指示する。VLAは映像を見ながら飛行動作を生成し、対象者を見失った場合は任務管理が再捜索や着陸に切り替える。離陸・見回しの旋回・着陸は通常の制御で実行する。',8.8)
p('VLAには画像・英語の工程指示・機体状態を入力し、過去の画像列や任務履歴は入力しない。上位の「青い服の人を探して」は直接渡さず、「Approach the person wearing blue and stop.」などに切り替える。人物の正解座標や検出器の検出枠は、VLAと実行部には渡さない。',8.5,color=GRAY,gap=0)

'''
text = text[:start] + section + text[end:]
assert text.count("p('描画：Blender',7.2,color=GRAY,gap=12)") == 1
text = text.replace("p('描画：Blender',7.2,color=GRAY,gap=12)", "p('物理：MuJoCo ／ 描画：Blender',7.2,color=GRAY,gap=12)")

# Highlight the VLA row through typography; all other rows retain equal weight.
old = "def cell(s,h=False):return Paragraph(escape(str(s)),ParagraphStyle('t',fontName='JB' if h else 'JP',fontSize=size,leading=size*1.55,wordWrap='CJK',textColor=colors.white if h else NAVY))"
new = "def cell(s,h=False,emphasis=False):return Paragraph(escape(str(s)),ParagraphStyle('t',fontName='JB' if h or emphasis else 'JP',fontSize=size,leading=size*1.55,wordWrap='CJK',textColor=colors.white if h else (TEAL if emphasis else NAVY)))"
assert text.count(old) == 1
text = text.replace(old, new)
old = "[[cell(v,True) for v in headers]]+[[cell(v) for v in row] for row in rows]"
new = "[[cell(v,True) for v in headers]]+[[cell(v,emphasis=row[0]=='SmolVLA') for v in row] for row in rows]"
assert text.count(old) == 1
text = text.replace(old, new)

text = text.replace('文言見直し01_全頁生成.pdf', '文言見直し02_全頁生成.pdf')
text = text.replace('reports/wording01/generated_', 'reports/wording02/generated_')
generated_source = work / 'build_report_wording02_generated.py'
generated_source.write_text(text, encoding='utf-8')
scope = {'__file__': str(BASE / 'scripts/build_report_rebuild03.py'), '__name__': '__main__'}
exec(compile(text, str(generated_source), 'exec'), scope)

old_reader = PdfReader(original)
new_reader = PdfReader(scope['OUT'])
assert len(old_reader.pages) == len(new_reader.pages) == 4
writer = PdfWriter()
writer.add_page(new_reader.pages[0])
for page in old_reader.pages[1:]:
    writer.add_page(page)
writer.add_metadata({'/Title': '災害救助ドローン / v1.1 検証更新版', '/Subject': 'Physical AI 応用1 最終課題'})
with output.open('wb') as f:
    writer.write(f)
final = PdfReader(output)
first = final.pages[0].extract_text()
compact = ''.join(first.split())
for phrase in ['自律飛行を支える役割分担', '飛行動作の生成を担うのが、SmolVLAである。', '物理：MuJoCo', '描画：Blender', '工程を切り替える判断を支援する。', '限られた人手']:
    assert ''.join(phrase.split()) in compact, phrase
assert first.index('SmolVLA\n映像と指示から') < first.index('任務管理プログラム')
assert 'VLAが人を認識し、近づき、止まる' not in first
for i in range(1, 4):
    assert final.pages[i].extract_text() == old_reader.pages[i].extract_text()
    assert final.pages[i].get_contents().get_data() == old_reader.pages[i].get_contents().get_data()
assert hashlib.sha256(original.read_bytes()).hexdigest() == old_hash
receipt = dict(output=str(output), pages=len(final.pages), sha256=hashlib.sha256(output.read_bytes()).hexdigest(), source_sha256=old_hash, source_unchanged=True, pages_2_to_4_content_streams_unchanged=True, visually_reviewed=False, created_utc=datetime.now(timezone.utc).isoformat())
(work / 'check.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(output)
