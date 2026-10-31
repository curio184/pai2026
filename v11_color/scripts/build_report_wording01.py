"""Apply the two user-approved editorial changes, preserving pages 2–4."""
from pathlib import Path
import hashlib
import json
import sys
from pypdf import PdfReader, PdfWriter

BASE = Path(__file__).resolve().parents[1]
PROJECT = BASE.parent
sys.path.insert(0, str(BASE / 'scripts'))
source = BASE / 'scripts/build_report_rebuild03.py'
original = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_検証更新版.pdf'
output = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し01.pdf'
work = BASE / 'reports/wording01'
work.mkdir(parents=True, exist_ok=True)

text = source.read_text(encoding='utf-8')
old = '人が立ち入りにくい建物を、小型ドローンで捜索する。機体ごとに人が操縦する負担を減らすため、言葉で任務を伝え、対象者を探して確認画像を残す仕組みを制作した。被災した建物を想定した1室で、一連の動作を検証した。'
new = '災害現場において、人が立ち入りにくい建物を小型ドローンで捜索する。限られた人手で迅速に捜索を進めるため、言葉で任務を伝えると、ドローンが自律的に対象者を探し、確認画像を残す仕組みを制作した。'
assert text.count(old) == 1
text = text.replace(old, new)
old = "('計画に追従して飛行',['実行部・ArduPilotで安定化','MuJoCoで物理状態を更新'])"
new = "('飛行制御・物理シミュレーション',['ArduPilotで姿勢を安定化','MuJoCoで機体の運動を計算'])"
assert text.count(old) == 1
text = text.replace(old, new)
old = "c.drawString(x+10,top-22,head);c.setFont('JP',8.2);c.setFillColor(NAVY)\n        for j,line in enumerate(lines):c.drawString(x+10,top-44-j*15,line)"
new = """\n        if i == 2:
            c.setFont('JB',9.5)
            c.drawString(x+10,top-18,'飛行制御・')
            c.drawString(x+10,top-30,'物理シミュレーション')
        else:
            c.drawString(x+10,top-22,head)
        c.setFont('JP',8.2);c.setFillColor(NAVY)
        for j,line in enumerate(lines):c.drawString(x+10,top-(49 if i == 2 else 44)-j*15,line)"""
assert text.count(old) == 1
text = text.replace(old, new)
old = "y=top-101;p('Blenderが次のカメラ画像を描画し、VLAへの入力に戻す',8.2,color=GRAY,gap=12)"
new = "y=top-101;p('飛行後のカメラ画像を入力へ戻す',8.2,bold=True,gap=2);p('描画：Blender',7.2,color=GRAY,gap=12)"
assert text.count(old) == 1
text = text.replace(old, new)

# Isolate generated artifacts and check receipts from the completed experiment.
text = text.replace('説明資料_PAI最終課題_v1.1_検証更新版.pdf', '説明資料_PAI最終課題_v1.1_文言見直し01_全頁生成.pdf')
text = text.replace('reports/report_rebuild03_extracted.txt', 'reports/wording01/generated_extracted.txt')
text = text.replace('reports/pdf_rebuild03_check.json', 'reports/wording01/generated_check.json')
generated_source = work / 'build_report_wording01_generated.py'
generated_source.write_text(text, encoding='utf-8')
scope = {'__file__': str(source), '__name__': '__main__'}
exec(compile(text, str(generated_source), 'exec'), scope)
generated = scope['OUT']

old_reader = PdfReader(original)
new_reader = PdfReader(generated)
assert len(old_reader.pages) == len(new_reader.pages) == 4
writer = PdfWriter()
writer.add_page(new_reader.pages[0])
for page in old_reader.pages[1:]:
    writer.add_page(page)
writer.add_metadata({'/Title': '災害救助ドローン / v1.1 検証更新版', '/Subject': 'Physical AI 応用1 最終課題'})
with output.open('wb') as f:
    writer.write(f)
final = PdfReader(output)
assert len(final.pages) == 4
first = final.pages[0].extract_text()
for phrase in ['限られた人手', 'MuJoCoで機体の運動を計算', '飛行後のカメラ画像を入力へ戻す', '描画：Blender']:
    assert phrase in first, phrase
assert '災害現場において、人が立ち入りにくい建物を小型ドローンで捜索する。' in first
assert 'Blenderが次のカメラ画像を描画し' not in first
for i in range(1, 4):
    assert final.pages[i].extract_text() == old_reader.pages[i].extract_text()
    assert final.pages[i].get_contents().get_data() == old_reader.pages[i].get_contents().get_data()
receipt = {
    'output': str(output), 'pages': 4,
    'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
    'source_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
    'pages_2_to_4_content_streams_unchanged': True,
    'visually_reviewed': False,
    'changes': ['Approved introductory paragraph', 'MuJoCo physics and ArduPilot control made prominent', 'Blender relegated to rendering credit'],
}
(work / 'check.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(output)
