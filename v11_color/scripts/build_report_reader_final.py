"""Finish the four-page reader-led report using existing, verified evidence."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,math,sys
import numpy as np
from pypdf import PdfReader,PdfWriter

BASE=Path(__file__).resolve().parents[1];PROJECT=BASE.parent
sys.path.insert(0,str(BASE/'scripts'))
original=PROJECT/'output/pdf/説明資料_PAI最終課題_3ページ版.pdf'
output=PROJECT/'output/pdf/説明資料_PAI最終課題_完成版.pdf'
work=PROJECT/'tmp/pdfs/reader_final';records=BASE/'reports/reader_final'
work.mkdir(parents=True,exist_ok=True);records.mkdir(parents=True,exist_ok=True)
original_hash=hashlib.sha256(original.read_bytes()).hexdigest()

def string_assignment(path,name):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    return next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets))

training_helper=string_assignment(BASE/'scripts/build_report_training_diagram01.py','helper')
training_helper=training_helper.replace('6成分 × 32ステップの動作列','0.1秒ごとの動作を32個並べる')
training_helper=training_helper.replace('この一組を教師データとして、SmolVLAに追加学習','この組を使い、SmolVLAに飛行動作を学習させる')
probe_helper=string_assignment(BASE/'scripts/build_report_restructured02.py','figure_helper')
probe_helper=probe_helper.replace('left_w=190;right_x=L+220;right_w=CW-220;pic_h=142.5','left_w=150;right_x=L+205;right_w=CW-205;pic_h=112.5')
pair=json.loads((BASE/'reports/training_diagram01/training_pair.json').read_text(encoding='utf-8'))
own=np.asarray(pair['state']);action=np.asarray(pair['action_physical_units']);horizontal_speed=np.linalg.norm(action[:,:2],axis=1)
image_file=BASE/pair['image_source']['path']
assert hashlib.sha256(image_file.read_bytes()).hexdigest()==pair['image_source']['sha256']

source=(BASE/'reports/wording08/build_report_wording08_generated.py').read_text(encoding='utf-8')
prefix=source[:source.index("start('IMPLEMENTATION'")]
old="OUT=BASE/('reports/output/pdf/説明資料_PAI最終課題_v1.1_検証レビュー.pdf' if review else 'reports/output/pdf/説明資料_PAI最終課題_v1.1_文言見直し08_全頁生成.pdf');OUT.parent.mkdir(parents=True,exist_ok=True)"
assert prefix.count(old)==1
prefix=prefix.replace(old,"OUT=PROJECT/'tmp/pdfs/reader_final/generated.pdf';OUT.parent.mkdir(parents=True,exist_ok=True)")
prefix=prefix.replace('def table(headers,rows,widths,size=8.8):','def table(headers,rows,widths,size=8.8,padding=6):')
prefix=prefix.replace("('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)","('TOPPADDING',(0,0),(-1,-1),padding),('BOTTOMPADDING',(0,0),(-1,-1),padding)")
body=(BASE/'scripts/report_reader_final_body.py').read_text(encoding='utf-8')
assembled=prefix+training_helper+probe_helper+body
(work/'generated_source.py').write_text(assembled,encoding='utf-8')
scope=dict(__file__=str(BASE/'scripts/build_report_rebuild03.py'),__name__='__main__',np=np,math=math,own=own,action=action,horizontal_speed=horizontal_speed,image_file=image_file)
exec(compile(assembled,str(work/'generated_source.py'),'exec'),scope)
generated=PdfReader(scope['OUT']);prior=PdfReader(original)
assert len(generated.pages)==4 and len(prior.pages)==3
writer=PdfWriter()
for page in generated.pages:writer.add_page(page)
writer.add_metadata({'/Title':'災害救助ドローン','/Subject':'Physical AI 応用1'})
with output.open('wb') as file:writer.write(file)
final=PdfReader(output)
assert len(final.pages)==4
assert final.pages[0].extract_text()==prior.pages[0].extract_text().replace('1 / 3','1 / 4')
full='\n'.join(page.extract_text() for page in final.pages);compact=''.join(full.split())
for phrase in ['飛行動作を学習させる','お手本の動作を作る','色・位置・距離を変えてデータを用意する','生成した動作で飛ばす','条件を変えて確かめる','16 / 16','64/64','0.08','25cm','未検証']:
    assert ''.join(phrase.split()) in compact,phrase
for phrase in ['v1.0','v1.1','旧版','新版','更新版','改善前','改善後','動画撮影後','人物位置はVLAへの入力には含めない。']:
    assert phrase not in full,phrase
for i,page in enumerate(final.pages,1):assert f'{i} / 4' in page.extract_text()
assert hashlib.sha256(original.read_bytes()).hexdigest()==original_hash
(records/'extracted.txt').write_text(full,encoding='utf-8')
evidence_paths=['results/all_trials_rebuild03.json','probe_rebuild03/outputs/summary.json','protocol/static_probe_rebuild03.json','reports/training_diagram01/training_pair.json','reports/three_pages01/variation_audit.json','reports/v11_training_visibility_train16.json']
receipt=dict(output=str(output),pages=4,pdf_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),source_sha256=original_hash,source_unchanged=True,page_1_text_unchanged_except_page_count=True,visually_reviewed=False,created_utc=datetime.now(timezone.utc).isoformat(),reader_questions=['What is it and how are roles divided?','What did the VLA learn, what is one example, and how were teaching data made?','How is the learned plan executed despite delay, and what was demonstrated?','Does it work outside the training layouts and react to instructions?'],evidence=[dict(path=p,sha256=hashlib.sha256((BASE/p).read_bytes()).hexdigest()) for p in evidence_paths],no_new_experiments=True)
(records/'check.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(output)
