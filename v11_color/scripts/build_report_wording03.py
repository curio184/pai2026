"""Apply mission-first narrative and table ordering to the approved PDF."""
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
source = BASE / 'scripts/build_report_wording02.py'
text = source.read_text(encoding='utf-8')
old = "p('飛行動作の生成を担うのが、SmolVLAである。カメラ映像と言葉による指示から、指定された人物への接近・減速・停止の動作を生成する。任務管理や検出器、飛行制御がそれを支え、離陸から捜索、着陸までの一連の動作を実現する。',9.2)"
new = """p('任務管理プログラムが、離陸から捜索、着陸までの手順を管理する。検出器が対象者の発見を確認すると、SmolVLAに「青い服の人に近づいて止まって」などと指示する。',9.2,gap=5)
p('SmolVLAは、カメラ映像と指示をもとに、進む方向や速度、減速して止まるタイミングを決める。実行部がその動作を飛行指令に変換し、ArduPilotが機体の姿勢を安定させる。',9.2)"""
assert text.count(old) == 1
text = text.replace(old, new)
vla = " ('SmolVLA','映像と指示から、指定された人物への移動方向・速度・減速・停止の動作を生成する。'),\n"
detector = " ('SSDlite＋色判定','指定した色の服を着た人を連続3画像で確認する。接近中も対象者が見えているかを調べ、工程を切り替える判断を支援する。'),\n"
assert text.count(vla) == text.count(detector) == 1
text = text.replace(vla, '').replace(detector, detector + vla)
old = "p('対象者が見つかると、任務管理がVLAに「青い服の人に近づいて止まって」などと指示する。VLAは映像を見ながら飛行動作を生成し、対象者を見失った場合は任務管理が再捜索や着陸に切り替える。離陸・見回しの旋回・着陸は通常の制御で実行する。',8.8)"
new = "p('接近中に対象者を見失った場合は、検出器の情報をもとに任務管理が再捜索や着陸に切り替える。離陸・見回しの旋回・着陸は通常の制御で実行する。',8.8)"
assert text.count(old) == 1
text = text.replace(old, new)
text = text.replace("original = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し01.pdf'", "original = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し02.pdf'")
text = text.replace("output = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し02.pdf'", "output = PROJECT / 'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し03.pdf'")
text = text.replace("work = BASE / 'reports/wording02'", "work = BASE / 'reports/wording03'")
text = text.replace("'文言見直し02_全頁生成.pdf')", "'文言見直し03_全頁生成.pdf')")
text = text.replace("'reports/wording02/generated_')", "'reports/wording03/generated_')")
text = text.replace("generated_source = work / 'build_report_wording02_generated.py'", "generated_source = work / 'build_report_wording03_generated.py'")
text = text.replace("'飛行動作の生成を担うのが、SmolVLAである。'", "'任務管理プログラムが、離陸から捜索、着陸までの手順を管理する。'")
old = "assert first.index('SmolVLA\\n映像と指示から') < first.index('任務管理プログラム')"
new = """table_text = first.split('担当\\n役割', 1)[1]
order = ['任務管理プログラム', 'SSDlite＋色判定', 'SmolVLA', '実行部', 'ArduPilot']
assert [table_text.index(item) for item in order] == sorted(table_text.index(item) for item in order)"""
assert text.count(old) == 1
text = text.replace(old, new)
namespace = {'__file__': str(source), '__name__': '__main__'}
exec(compile(text, str(Path(__file__)), 'exec'), namespace)
