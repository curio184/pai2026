"""Present purpose, mechanism, challenges, design and results without version history."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,sys
import numpy as np
from pypdf import PdfReader,PdfWriter

BASE=Path(__file__).resolve().parents[1]
PROJECT=BASE.parent
sys.path.insert(0,str(BASE/'scripts'))
source=BASE/'reports/wording08/build_report_wording08_generated.py'
body=BASE/'scripts/report_restructured02_body.py'
original=PROJECT/'output/pdf/説明資料_PAI最終課題_構成見直し版.pdf'
output=PROJECT/'output/pdf/説明資料_PAI最終課題_構成整理版.pdf'
work=PROJECT/'tmp/pdfs/restructure02'
records=BASE/'reports/restructure02'
work.mkdir(parents=True,exist_ok=True);records.mkdir(parents=True,exist_ok=True)
original_hash=hashlib.sha256(original.read_bytes()).hexdigest()
text=source.read_text(encoding='utf-8')
prefix=text[:text.index("start('IMPLEMENTATION'")]
old="OUT=BASE/('reports/output/pdf/説明資料_PAI最終課題_v1.1_検証レビュー.pdf' if review else 'reports/output/pdf/説明資料_PAI最終課題_v1.1_文言見直し08_全頁生成.pdf');OUT.parent.mkdir(parents=True,exist_ok=True)"
assert prefix.count(old)==1
prefix=prefix.replace(old,"OUT=PROJECT/'tmp/pdfs/restructure02/generated.pdf';OUT.parent.mkdir(parents=True,exist_ok=True)")
scope={'__file__':str(BASE/'scripts/build_report_rebuild03.py'),'__name__':'__main__'}

figure_helper=r'''
def probe_single_model_figure():
    global y
    plan=read(BASE/'protocol/static_probe_rebuild03.json')
    fid=1
    assert fid in plan['figure_ids'], 'Keep the same preregistered example'
    f=next(row for row in plan['frames'] if row['id']==fid)
    rows=[json.loads(line) for line in (BASE/'probe_rebuild03/outputs/raw_outputs.jsonl').read_text(encoding='utf-8').splitlines()]
    rows=[row for row in rows if row['model']=='v1.1' and row['frame']['id']==fid and row['prompt_group']=='runtime_english']
    assert len(rows)==2
    layouts=read(BASE/'protocol/rebuild_final_layouts.json')['heldout_layouts']
    layout=next(row for row in layouts if row['name']==f['scene'])
    positions=np.asarray(layout['positions'])[:,:2]
    q=np.asarray(f['qpos'])
    image_file=BASE/'probe_rebuild03/images'/f'{fid:05d}.jpg'
    for row in rows:
        assert hashlib.sha256(image_file.read_bytes()).hexdigest()==row['image_sha256']
        mean=np.asarray(row['action_chunk'])[:10,:2].mean(axis=0)
        assert np.allclose(mean,row['body_horizontal'],atol=1e-6,rtol=0)
    top=y
    left_w=190;right_x=L+220;right_w=CW-220;pic_h=142.5
    c.setFillColor(NAVY);c.setFont('JB',9.3)
    c.drawString(L,top-12,'VLAへの入力画像')
    c.drawString(right_x,top-12,'指示ごとの動作の向き（上から見た図）')
    c.drawImage(str(image_file),L,top-24-pic_h,width=left_w,height=pic_h)
    plot_top=top-24;plot_bottom=plot_top-pic_h
    c.setStrokeColor(LINE);c.rect(right_x,plot_bottom,right_w,pic_h,stroke=1,fill=0)
    plot_scale=min(right_w/3.3,pic_h/2.7)
    plot_left=right_x+(right_w-3.3*plot_scale)/2
    def xy(v):
        return plot_left+float(v[0])*plot_scale,plot_bottom+(float(v[1])+1.35)*plot_scale
    sx,sy=xy(q[:2])
    for row in rows:
        color=row['color'];paint=colors.HexColor('#167CCA' if color=='blue' else '#D44946')
        actor=f['blue_actor'] if color=='blue' else 1-f['blue_actor']
        target=positions[actor]+[-.9,0]
        tx,ty=xy(target);c.setFillColor(paint);c.circle(tx,ty,3.5,fill=1,stroke=0)
        velocity=np.asarray(row['world_horizontal']);norm=np.linalg.norm(velocity)
        assert norm>=.02 and row['correct_goal']
        ex,ey=xy(q[:2]+velocity/norm*1.3)
        c.setStrokeColor(paint);c.setLineWidth(1.8);c.line(sx,sy,ex,ey)
        angle=math.atan2(ey-sy,ex-sx)
        for delta in (-.45,.45):
            c.line(ex,ey,ex-6*math.cos(angle+delta),ey-6*math.sin(angle+delta))
    c.setFillColor(NAVY);path=c.beginPath();path.moveTo(sx,sy+4);path.lineTo(sx-4,sy-4);path.lineTo(sx+4,sy-4);path.close();c.drawPath(path,fill=1,stroke=0)
    c.setFont('JP',8.2);c.setFillColor(GRAY)
    c.drawString(L,plot_bottom-16,'青の矢印：青い服の人への指示　赤の矢印：赤い服の人への指示')
    c.drawString(L,plot_bottom-30,'丸：各人物の前の目標点　三角：機体')
    c.setLineWidth(1)
    y=plot_bottom-44
'''
assembled=prefix+figure_helper+body.read_text(encoding='utf-8')
(work/'generated_source.py').write_text(assembled,encoding='utf-8')
scope.update(np=np,math=math)
exec(compile(assembled,str(work/'generated_source.py'),'exec'),scope)
generated=PdfReader(scope['OUT']);prior=PdfReader(original)
assert len(generated.pages)==len(prior.pages)==4
writer=PdfWriter();writer.add_page(prior.pages[0])
for page in generated.pages[1:]:writer.add_page(page)
writer.add_metadata({'/Title':'災害救助ドローン','/Subject':'Physical AI 応用1'})
with output.open('wb') as file:writer.write(file)
final=PdfReader(output)
assert final.pages[0].get_contents().get_data()==prior.pages[0].get_contents().get_data()
full='\n'.join(page.extract_text() for page in final.pages)
for forbidden in ['v1.0','v1.1','旧版','新版','更新版','改善前','改善後','動画撮影後','再現確認']:
    assert forbidden not in full,forbidden
for phrase in ['人物の位置を暗記させない','推論中の機体の移動を補正する','16 / 16','64/64','0.08','25cm','連続3画像','50g','未検証']:
    assert ''.join(phrase.split()) in ''.join(full.split()),phrase
assert hashlib.sha256(original.read_bytes()).hexdigest()==original_hash
(records/'extracted.txt').write_text(full,encoding='utf-8')
receipt=dict(output=str(output),pages=4,pdf_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),source_sha256=original_hash,source_unchanged=True,page_1_content_stream_unchanged=True,visually_reviewed=False,created_utc=datetime.now(timezone.utc).isoformat(),content_focus=['purpose','mechanism','challenges','design_choices','results'],version_history_and_baseline_comparison_omitted=True,evaluation_model_sha256=scope['selected']['checkpoint_sha256'],main_results_source='results/all_trials_rebuild03.json',probe_source='probe_rebuild03/outputs/raw_outputs.jsonl',probe_figure_id=1,figure_method='Vector plot of preregistered example from final-model raw outputs; original JPEG drawn unchanged; no inference or flight performed.',full_history_preserved_in_existing_readme=True)
(records/'check.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(output)
