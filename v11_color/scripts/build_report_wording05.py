"""Align prose, table hierarchy and the flight-control loop with reader intent."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
from pypdf import PdfReader, PdfWriter

BASE = Path(__file__).resolve().parents[1]
PROJECT = BASE.parent
sys.path.insert(0, str(BASE / 'scripts'))
source = BASE / 'reports/wording04/build_report_wording04_generated.py'
original = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し04.pdf'
output = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し05.pdf'
work = BASE / 'reports/wording05'
work.mkdir(parents=True, exist_ok=True)
source_hash = hashlib.sha256(original.read_bytes()).hexdigest()
text = source.read_text(encoding='utf-8')
start = text.index("label('自律飛行を支える役割分担')")
end = text.index("start('IMPLEMENTATION'", start)
section = '''label('自律飛行を支える役割分担')
p('任務管理プログラムが、離陸から捜索、着陸までの手順を管理する。接近の工程では、SmolVLAに「青い服の人に近づいて止まって」などと指示する。',9.2,gap=5)
p('SmolVLAは、カメラ映像と指示をもとに、近づく相手や移動方向、速度、減速して止まるタイミングを決める。実行部が撮影後の機体の動きを補正して飛行指令を出し、ArduPilotが機体の姿勢を安定させる。',9.2)
table(['担当','役割'],[
 ('任務管理プログラム','各工程の完了を判断し、次の工程へ切り替える。接近の工程では、SmolVLAに対象者への接近・停止を指示する。'),
 ('SmolVLA','画像・指示・機体の状態から、指定された人物への接近・減速・停止の動作列を生成する。'),
 ('実行部','VLAの動作列が示す到達先へ向けて飛行指令を出す。撮影後に機体が動いた分を補正する。'),
 ('ArduPilot','飛行指令に応じてモーターを調整し、機体の姿勢を安定させる。'),
 ('SSDlite＋色判定','工程の切り替えを支援するため、対象者が見えているかを確認し、結果を任務管理へ返す。')],[108,CW-108],size=8.7)
p('工程の区切りを判断するために、SSDliteと服の色判定を併用する。指定された服色の人物を連続3画像で確認し、接近中も見失っていないかを調べる。任務管理プログラムは、その情報と機体の状態をもとに、次の工程へ進むか、再捜索や着陸に切り替えるかを判断する。',8.8)
p('離陸・見回しの旋回・着陸は通常の制御で実行する。VLAへの指示は「Approach the person wearing blue and stop.」などの英語の工程指示とし、上位の「青い服の人を探して」は直接渡さない。過去の画像列や任務履歴、人物の正解座標や検出器の検出枠もVLAには渡さず、実行部も人物の正解座標や検出枠を使わない。',8.5,color=GRAY,gap=0)

'''
text = text[:start] + section + text[end:]

# Make the supporting detector row visually distinct from the command flow.
old = "    _,h=t.wrap(CW,1000);assert y-h>46,(page,'table',y,h);t.drawOn(c,L,y-h);y-=h+10"
new = """    if rows and str(rows[-1][0]).startswith('SSDlite＋色判定'):
        t.setStyle(TableStyle([('LINEABOVE',(0,len(rows)),(-1,len(rows)),0.8,LINE),('TOPPADDING',(0,len(rows)),(-1,len(rows)),9),('BACKGROUND',(0,len(rows)),(-1,len(rows)),colors.HexColor('#F4F6F6'))]))
    _,h=t.wrap(CW,1000);assert y-h>46,(page,'table',y,h);t.drawOn(c,L,y-h);y-=h+10"""
assert text.count(old) == 1
text = text.replace(old, new)

# The existing diagram depicts the VLA's feedback loop, not the mission hierarchy.
# Label that scope explicitly so the diagram and role table have clear purposes.
old = "p('離陸 → 見回し → 発見確認 → 接近・停止 → 確認画像の保存 → 着陸',9.3,True,12)\ndiagram()"
new = "p('離陸 → 見回し → 発見確認 → 接近・停止 → 確認画像の保存 → 着陸',9.3,True,9)\np('接近・停止の飛行制御',8.2,True,6,TEAL)\ndiagram()"
assert text.count(old) == 1
text = text.replace(old, new)
text = text.replace('文言見直し04_全頁生成.pdf', '文言見直し05_全頁生成.pdf')
text = text.replace('reports/wording04/generated_', 'reports/wording05/generated_')
generated_source = work / 'build_report_wording05_generated.py'
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
for phrase in ['自律飛行を支える役割分担', '接近・停止の飛行制御', '工程の切り替えを支援するため', '任務管理プログラムは、その情報と機体の状態をもとに', '連続3画像', '物理：MuJoCo', '描画：Blender', '限られた人手']:
    assert ''.join(phrase.split()) in compact, phrase
assert '検出器が対象者の発見を確認すると' not in compact
for i in range(1, 4):
    assert final.pages[i].extract_text() == old_reader.pages[i].extract_text()
    assert final.pages[i].get_contents().get_data() == old_reader.pages[i].get_contents().get_data()
assert hashlib.sha256(original.read_bytes()).hexdigest() == source_hash
receipt = dict(output=str(output), pages=4, sha256=hashlib.sha256(output.read_bytes()).hexdigest(), source_sha256=source_hash, source_unchanged=True, pages_2_to_4_content_streams_unchanged=True, visually_reviewed=False, created_utc=datetime.now(timezone.utc).isoformat(), intent='Communicate the whole system accurately to judges, with VLA central to image-based movement generation and detector as support for mission-stage decisions.', role_order=order)
(work / 'check.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(output)
