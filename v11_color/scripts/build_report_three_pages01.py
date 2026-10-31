"""Three-page report: system, varied training/evaluation, and concise evidence."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,math,sys
import numpy as np
from pypdf import PdfReader,PdfWriter

BASE=Path(__file__).resolve().parents[1];PROJECT=BASE.parent
sys.path.insert(0,str(BASE/'scripts'))
original=PROJECT/'output/pdf/説明資料_PAI最終課題_学習図解版.pdf'
output=PROJECT/'output/pdf/説明資料_PAI最終課題_3ページ版.pdf'
work=PROJECT/'tmp/pdfs/three_pages01';records=BASE/'reports/three_pages01'
work.mkdir(parents=True,exist_ok=True);records.mkdir(parents=True,exist_ok=True)
original_hash=hashlib.sha256(original.read_bytes()).hexdigest()

def string_assignment(path,name):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    return next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets))

training_helper=string_assignment(BASE/'scripts/build_report_training_diagram01.py','helper')
probe_helper=string_assignment(BASE/'scripts/build_report_restructured02.py','figure_helper')
# Keep camera images at their true aspect ratio; compact the counterfactual figure.
probe_helper=probe_helper.replace('left_w=190;right_x=L+220;right_w=CW-220;pic_h=142.5','left_w=160;right_x=L+205;right_w=CW-205;pic_h=120')
pair=json.loads((BASE/'reports/training_diagram01/training_pair.json').read_text(encoding='utf-8'))
own=np.asarray(pair['state']);action=np.asarray(pair['action_physical_units']);horizontal_speed=np.linalg.norm(action[:,:2],axis=1)
image_file=BASE/pair['image_source']['path']
assert hashlib.sha256(image_file.read_bytes()).hexdigest()==pair['image_source']['sha256']

# Audit the actual variation present in the training-frame specification.
plan=json.loads((BASE/'protocol/plan.json').read_text(encoding='utf-8'))
frames=json.loads((BASE/'protocol/training_frames.json').read_text(encoding='utf-8'))
distances=[]
for frame in frames:
    people=np.asarray(plan['train_layouts'][frame['layout']]['positions'])[:,:2]
    q=np.asarray(frame['qpos'])[:2]
    distances.extend(np.linalg.norm(people-q,axis=1).tolist())
assert len(plan['train_layouts'])==20 and max(distances)-min(distances)>1
variation=dict(training_layouts=20,training_horizontal_distance_range_m=[min(distances),max(distances)],shirt_assignments=sorted(set(f['blue_actor'] for f in frames)),visual_perturbation='Evaluated fog/dust, not an assertion of Gaussian pixel-noise augmentation',sources=['protocol/training_frames.json','protocol/plan.json','protocol/rebuild_final_layouts.json','reports/v11_training_visibility_train16.json'])
(records/'variation_audit.json').write_text(json.dumps(variation,indent=2),encoding='utf-8')

source=(BASE/'reports/wording08/build_report_wording08_generated.py').read_text(encoding='utf-8')
prefix=source[:source.index("start('IMPLEMENTATION'")]
old="OUT=BASE/('reports/output/pdf/説明資料_PAI最終課題_v1.1_検証レビュー.pdf' if review else 'reports/output/pdf/説明資料_PAI最終課題_v1.1_文言見直し08_全頁生成.pdf');OUT.parent.mkdir(parents=True,exist_ok=True)"
assert prefix.count(old)==1
prefix=prefix.replace(old,"OUT=PROJECT/'tmp/pdfs/three_pages01/generated.pdf';OUT.parent.mkdir(parents=True,exist_ok=True)")
assert prefix.count("f'{page} / 4'")==1
prefix=prefix.replace("f'{page} / 4'","f'{page} / 3'")
assembled=prefix+training_helper+probe_helper+(BASE/'scripts/report_three_pages01_body.py').read_text(encoding='utf-8')
(work/'generated_source.py').write_text(assembled,encoding='utf-8')
scope=dict(__file__=str(BASE/'scripts/build_report_rebuild03.py'),__name__='__main__',np=np,math=math,own=own,action=action,horizontal_speed=horizontal_speed,image_file=image_file)
exec(compile(assembled,str(work/'generated_source.py'),'exec'),scope)
generated=PdfReader(scope['OUT']);prior=PdfReader(original)
assert len(generated.pages)==3 and len(prior.pages)==4
writer=PdfWriter()
for page in generated.pages:writer.add_page(page)
writer.add_metadata({'/Title':'災害救助ドローン','/Subject':'Physical AI 応用1'})
with output.open('wb') as file:writer.write(file)
final=PdfReader(output)
assert len(final.pages)==3
assert final.pages[0].extract_text()==prior.pages[0].extract_text().replace('1 / 4','1 / 3')
full='\n'.join(p.extract_text() for p in final.pages)
compact=''.join(full.split())
for phrase in ['条件を変えて学習・検証','同じ場面の丸暗記に頼らないよう','人物の位置・距離','服の色・指示','霧・粉じん','16 / 16','64 / 64','9 / 9','0.08','25cm','未検証']:
    assert ''.join(phrase.split()) in compact,phrase
for forbidden in ['v1.0','v1.1','旧版','新版','更新版','改善前','改善後','動画撮影後']:
    assert forbidden not in full,forbidden
for i,page in enumerate(final.pages,1):assert f'{i} / 3' in page.extract_text()
assert hashlib.sha256(original.read_bytes()).hexdigest()==original_hash
(records/'extracted.txt').write_text(full,encoding='utf-8')
receipt=dict(output=str(output),pages=3,pdf_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),source_sha256=original_hash,source_unchanged=True,page_1_text_unchanged_except_page_count=True,visually_reviewed=False,created_utc=datetime.now(timezone.utc).isoformat(),reader_structure=['purpose_and_system','varied_training_and_evaluation','results_and_scope'],variation_audit='variation_audit.json',noise_scope='Fog/dust visual conditions only; no unverified image-noise claim',training_example_source='reports/training_diagram01/training_pair.json',probe_example_id=1,no_new_experiments=True)
(records/'check.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(output)
