"""Illustrate one actual supervised training pair, changing only report page 2."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
import numpy as np
from pypdf import PdfReader,PdfWriter

BASE=Path(__file__).resolve().parents[1]
PROJECT=BASE.parent
sys.path.insert(0,str(BASE/'scripts'))
original=PROJECT/'output/pdf/説明資料_PAI最終課題_構成整理版.pdf'
output=PROJECT/'output/pdf/説明資料_PAI最終課題_学習図解版.pdf'
work=PROJECT/'tmp/pdfs/training_diagram01'
records=BASE/'reports/training_diagram01'
work.mkdir(parents=True,exist_ok=True);records.mkdir(parents=True,exist_ok=True)
original_hash=hashlib.sha256(original.read_bytes()).hexdigest()

dataset=BASE/'data/dataset16_en'
sources=json.loads((dataset/'image_sources.json').read_text(encoding='utf-8'))
sample_index=296
with np.load(dataset/'audited_samples.npz') as data:
    image_id=int(data['image'][sample_index])
    task=int(data['task'][sample_index])
    own=data['state'][sample_index].copy()
    action=data['action'][sample_index].copy()*np.array([.2,.2,.3,.35,1,1])
assert task==0 and action.shape==(32,6) and image_id==34
source_row=next(row for row in sources if row['id']==image_id)
image_file=BASE/source_row['path']
assert hashlib.sha256(image_file.read_bytes()).hexdigest()==source_row['sha256']
horizontal_speed=np.linalg.norm(action[:,:2],axis=1)
assert horizontal_speed[0]>.08 and horizontal_speed[-1]<.03
(records/'training_pair.json').write_text(json.dumps(dict(sample_index=sample_index,image_id=image_id,image_source=source_row,state=own.tolist(),instruction='Approach the person wearing blue and stop.',action_physical_units=action.tolist(),dataset_audit_sha256=hashlib.sha256((dataset/'audit.json').read_bytes()).hexdigest(),displayed_plot='Magnitude of horizontal teacher velocity over 32 steps, 0.1 seconds per step'),ensure_ascii=False,indent=2),encoding='utf-8')

text=(BASE/'reports/wording08/build_report_wording08_generated.py').read_text(encoding='utf-8')
prefix=text[:text.index("start('IMPLEMENTATION'")]
old="OUT=BASE/('reports/output/pdf/説明資料_PAI最終課題_v1.1_検証レビュー.pdf' if review else 'reports/output/pdf/説明資料_PAI最終課題_v1.1_文言見直し08_全頁生成.pdf');OUT.parent.mkdir(parents=True,exist_ok=True)"
assert prefix.count(old)==1
prefix=prefix.replace(old,"OUT=PROJECT/'tmp/pdfs/training_diagram01/generated.pdf';OUT.parent.mkdir(parents=True,exist_ok=True)")
helper=r'''
def training_pair_diagram():
    global y
    top=y;box_h=156;input_w=310;gap=22;out_x=L+input_w+gap;out_w=CW-input_w-gap
    c.setFillColor(LIGHT);c.roundRect(L,top-box_h,input_w,box_h,5,fill=1,stroke=0)
    c.setFillColor(colors.HexColor('#F0F5F7'));c.roundRect(out_x,top-box_h,out_w,box_h,5,fill=1,stroke=0)
    c.setFillColor(TEAL);c.setFont('JB',10)
    c.drawString(L+12,top-19,'入力')
    c.drawString(out_x+12,top-19,'対応するお手本の動作')
    c.drawImage(str(image_file),L+12,top-128,width=120,height=90)
    c.setFont('JP',8);c.setFillColor(GRAY);c.drawString(L+12,top-143,'カメラ画像')
    tx=L+145
    c.setFillColor(NAVY);c.setFont('JB',8.6);c.drawString(tx,top-43,'言葉の指示（日本語訳）')
    c.setFont('JP',9.2);c.drawString(tx,top-60,'青い服の人に')
    c.drawString(tx,top-75,'近づいて止まって')
    c.setFont('JB',8.6);c.drawString(tx,top-99,'機体の状態')
    c.setFont('JP',8.6);c.drawString(tx,top-115,f'高度 {own[3]:.2f}m')
    c.drawString(tx,top-130,f'水平速度 {np.linalg.norm(own[:2]):.2f}m/s など')
    cy=top-80
    c.setStrokeColor(TEAL);c.setLineWidth(1.2);c.line(L+input_w+3,cy,out_x-3,cy)
    c.line(out_x-3,cy,out_x-7,cy+3);c.line(out_x-3,cy,out_x-7,cy-3)
    c.setFillColor(GRAY);c.setFont('JP',8);c.drawString(out_x+12,top-36,'水平速度の例（m/s）')
    gx=out_x+32;gy=top-112;gw=out_w-46;gh=62
    c.setStrokeColor(LINE);c.setLineWidth(.5);c.line(gx,gy,gx+gw,gy);c.line(gx,gy,gx,gy+gh)
    c.setFont('JP',7.2);c.setFillColor(GRAY)
    c.drawRightString(gx-4,gy-2,'0');c.drawRightString(gx-4,gy+gh-2,'0.2')
    c.drawString(gx,gy-12,'0');c.drawRightString(gx+gw,gy-12,'3.1秒')
    c.setStrokeColor(TEAL);c.setLineWidth(1.5)
    points=[(gx+i/31*gw,gy+float(v)/.2*gh) for i,v in enumerate(horizontal_speed)]
    path=c.beginPath();path.moveTo(*points[0])
    for point in points[1:]:path.lineTo(*point)
    c.drawPath(path,stroke=1,fill=0)
    c.setFillColor(GRAY);c.setFont('JP',7.7);c.drawString(out_x+12,top-143,'6成分 × 32ステップの動作列')
    bottom=top-box_h
    c.setStrokeColor(LINE);c.setLineWidth(.8)
    c.line(L+input_w/2,bottom-4,L+input_w/2,bottom-13)
    c.line(L+input_w/2,bottom-13,out_x+out_w/2,bottom-13)
    c.line(out_x+out_w/2,bottom-13,out_x+out_w/2,bottom-4)
    c.setFillColor(NAVY);c.setFont('JB',9.4)
    c.drawCentredString(L+CW/2,bottom-30,'この一組を教師データとして、SmolVLAに追加学習')
    c.setLineWidth(1)
    y=bottom-43
'''
body=(BASE/'scripts/report_training_diagram01_body.py').read_text(encoding='utf-8')
assembled=prefix+helper+body
(work/'generated_source.py').write_text(assembled,encoding='utf-8')
scope=dict(__file__=str(BASE/'scripts/build_report_rebuild03.py'),__name__='__main__',np=np,own=own,action=action,horizontal_speed=horizontal_speed,image_file=image_file)
exec(compile(assembled,str(work/'generated_source.py'),'exec'),scope)
generated=PdfReader(scope['OUT']);prior=PdfReader(original)
assert len(generated.pages)==2 and len(prior.pages)==4
writer=PdfWriter()
writer.add_page(prior.pages[0]);writer.add_page(generated.pages[1])
for page in prior.pages[2:]:writer.add_page(page)
writer.add_metadata({'/Title':'災害救助ドローン','/Subject':'Physical AI 応用1'})
with output.open('wb') as file:writer.write(file)
final=PdfReader(output)
assert len(final.pages)==4
for i in [0,2,3]:
    assert final.pages[i].get_contents().get_data()==prior.pages[i].get_contents().get_data()
    assert final.pages[i].extract_text()==prior.pages[i].extract_text()
text='\n'.join(page.extract_text() for page in final.pages)
for phrase in ['一組の教師データ','対応するお手本の動作','6成分','32ステップ','この一組を教師データとして']:
    assert ''.join(phrase.split()) in ''.join(text.split())
for forbidden in ['v1.0','v1.1','旧版','新版','更新版','改善前','改善後','動画撮影後','人物の位置に頼らず相手を選ぶことと']:
    assert forbidden not in text
assert hashlib.sha256(original.read_bytes()).hexdigest()==original_hash
(records/'extracted.txt').write_text(text,encoding='utf-8')
receipt=dict(output=str(output),pages=4,pdf_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),source_sha256=original_hash,source_unchanged=True,pages_1_3_4_content_streams_unchanged=True,visually_reviewed=False,created_utc=datetime.now(timezone.utc).isoformat(),training_pair_source='data/dataset16_en/audited_samples.npz',sample_index=sample_index,image_id=image_id,teacher_velocity_graph_from_actual_label=True,no_new_training_or_inference=True)
(records/'check.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(output)
