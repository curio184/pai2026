"""Rebuild the report around the approved reader-question tree; retain page 1."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
from pypdf import PdfReader, PdfWriter

BASE=Path(__file__).resolve().parents[1]
PROJECT=BASE.parent
sys.path.insert(0,str(BASE/'scripts'))
source=BASE/'reports/wording08/build_report_wording08_generated.py'
body=BASE/'scripts/report_restructured01_body.py'
original=PROJECT/'output/pdf/説明資料_PAI最終課題_v1.1_文言見直し08.pdf'
output=PROJECT/'output/pdf/説明資料_PAI最終課題_構成見直し版.pdf'
work=PROJECT/'tmp/pdfs/restructure01'
records=BASE/'reports/restructure01'
work.mkdir(parents=True,exist_ok=True)
records.mkdir(parents=True,exist_ok=True)
original_hash=hashlib.sha256(original.read_bytes()).hexdigest()

text=source.read_text(encoding='utf-8')
prefix=text[:text.index("start('IMPLEMENTATION'")]
old="OUT=BASE/('reports/output/pdf/説明資料_PAI最終課題_v1.1_検証レビュー.pdf' if review else 'reports/output/pdf/説明資料_PAI最終課題_v1.1_文言見直し08_全頁生成.pdf');OUT.parent.mkdir(parents=True,exist_ok=True)"
new="OUT=PROJECT/'tmp/pdfs/restructure01/generated.pdf';OUT.parent.mkdir(parents=True,exist_ok=True)"
assert prefix.count(old)==1
prefix=prefix.replace(old,new)
assembled=prefix+body.read_text(encoding='utf-8')
(work/'generated_source.py').write_text(assembled,encoding='utf-8')
scope={'__file__':str(BASE/'scripts/build_report_rebuild03.py'),'__name__':'__main__'}
exec(compile(assembled,str(work/'generated_source.py'),'exec'),scope)

generated=PdfReader(scope['OUT'])
previous=PdfReader(original)
assert len(generated.pages)==len(previous.pages)==4
writer=PdfWriter()
writer.add_page(previous.pages[0])
for page in generated.pages[1:]:writer.add_page(page)
writer.add_metadata({'/Title':'災害救助ドローン','/Subject':'Physical AI 応用1'})
with output.open('wb') as f:writer.write(f)
final=PdfReader(output)
assert len(final.pages)==4
assert final.pages[0].get_contents().get_data()==previous.pages[0].get_contents().get_data()
extracted=[p.extract_text() for p in final.pages]
full='\n'.join(extracted)
for phrase in ['お手本の動作を作る','位置に頼らず','推論中の機体の移動','03  実演結果','04  検証','0.08','25cm','連続3画像','32画像','16 / 16','64/64','50g','未検証']:
    assert ''.join(phrase.split()) in ''.join(full.split()),phrase
assert '最終課題・v1.1 検証更新版' not in full
assert extracted[1].index('お手本の動作を作る')<extracted[1].index('位置に頼らず')<extracted[1].index('推論中の機体の移動')
assert hashlib.sha256(original.read_bytes()).hexdigest()==original_hash
(records/'extracted.txt').write_text(full,encoding='utf-8')
receipt=dict(output=str(output),pages=4,pdf_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),source_sha256=original_hash,source_unchanged=True,page_1_content_stream_unchanged=True,visually_reviewed=False,created_utc=datetime.now(timezone.utc).isoformat(),reader_structure=['purpose_and_system','teacher_learning_execution','demonstration_results','validation_and_scope'],evidence_paths=['results/all_trials_rebuild03.json','probe_rebuild03/outputs/summary.json','probe_v10_language/outputs/summary.json','reports/v11_training_visibility_train16.json','reports/rebuild_latency_same_case.json'],details_retained_in_existing_readme=['full_training_lineage_and_settings','T5_historical_learning_comparisons','complete_failure_records','protocols_and_acceptance_thresholds','teacher_and_tracking_equations'])
(records/'check.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(output)
