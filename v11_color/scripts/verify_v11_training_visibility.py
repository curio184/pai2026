"""Read-only provenance audit of v1.1 training image visibility conditions."""
import datetime,hashlib,io,json
from pathlib import Path
from PIL import Image
W=Path(__file__).resolve().parents[1];P=W.parent;R=P.parent/'repository';V=P/'validation_v1_1'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=W/'reports/v11_training_visibility_scope.json';assert not out.exists()
    inspection=read(V/'results/T6_scene_inspection.json'); bysha={r['sha256']:r for r in inspection}
    manifests=[]
    for name,script,count in [('render_manifest.json','render_training.py',4000),('render05_manifest.json','render_training05.py',2000)]:
        p=W/'data'/name;m=read(p)
        assert sha(W/'scripts'/script)==m['script_sha256']
        assert sha(P/'tmp/rescue_search/scenes/clear/scene.blend')==m['source_blend_sha256']
        nodes=bysha[m['source_blend_sha256']]['volume_nodes'];assert len(nodes)==1
        node=nodes[0];assert abs(node['density']-.004)<1e-8 and not node['density_linked'] and not node['animated']
        assert m['density']==.004
        manifests.append(dict(path='data/'+name,sha256=sha(p),render_script_sha256=m['script_sha256'],
            source_blend_sha256=m['source_blend_sha256'],images=count,density=node['density']))
    retained=P/'outputs/vla_data_realism_precision_02';oldhash=read(retained/'image_checksums.json')
    oldnames={int(Path(n).stem):n for n in oldhash}
    retained_provenance=next(r for r in read(V/'results/T6_verified_scope.json')['training'] if r['dataset']==retained.name)
    assert sha(retained/'manifest.json')==retained_provenance['manifest_sha256']
    assert len(oldhash)==2408
    for r in retained_provenance['scene_provenance']:
        assert sha(P/r['scene'])==r['sha256']
        for node in bysha[r['sha256']]['volume_nodes']:
            assert abs(node['density']-.004)<1e-8 and not node['density_linked'] and not node['animated']
    sources=read(W/'data/dataset13_en/image_sources.json');assert len(sources)==8408
    counts={0:0,1:0,2:0};seen=set()
    for r in sources:
        path=W/r['path'];actual=sha(path);assert actual==r['sha256'];seen.add(actual)
        i=r['id'];domain=r['domain'];counts[domain]+=1
        if domain==1:
            name=oldnames[i-4000];assert sha(retained/'images'/name)==actual==oldhash[name]
        else:
            png=W/('data/rendered_png' if domain==0 else 'data/rendered05_png')/f'{i if domain==0 else i-6408:05d}.png'
            buf=io.BytesIO()
            with Image.open(png) as image:image.convert('RGB').save(buf,format='JPEG',quality=70)
            assert hashlib.sha256(buf.getvalue()).hexdigest()==actual,(i,'rendered PNG to training JPEG differs')
        if sum(counts.values())%2000==0:print(json.dumps(dict(images_checked=sum(counts.values()))),flush=True)
    assert counts=={0:4000,1:2408,2:2000}
    evaluation=R/'rescue_search/runs/eval03';assert evaluation.exists()
    evaluation_files=list(evaluation.rglob('*.jpg'));assert evaluation_files
    overlap=[str(p.relative_to(R)) for p in evaluation_files if sha(p) in seen];assert not overlap
    result=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verified=True,
        scope='The8408 available v1.1 adaptation images only, not the foundation model pretraining corpus or all historical data.',
        dataset='data/dataset13_en',dataset_audit_sha256=sha(W/'data/dataset13_en/audit.json'),
        image_source_manifest_sha256=sha(W/'data/dataset13_en/image_sources.json'),images=8408,domain_counts=counts,
        all_training_image_hashes_match=True,new_images_match_saved_rendered_PNGs_after_registered_JPEG_conversion=True,
        retained_images_byte_identical=True,render_manifests=manifests,
        prior_node_inspection_sha256=sha(V/'results/T6_scene_inspection.json'),
        retained_provenance=retained_provenance['scene_provenance'],documented_training_density=.004,
        evaluation_conditions=read(V/'results/T6_verified_scope.json')['conditions'],
        evaluation_jpegs_checked=len(evaluation_files),exact_evaluation_image_overlap=overlap,
        caveat='15-30x is the renderer density-parameter ratio, not physical visibility or particle concentration. Hash non-overlap does not establish independence of scene content. Discovery belongs to the detector; VLA claims concern generated flight behavior.',
        policy_inferences=0,optimizer_updates=0,images_modified=False)
    out.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(dict(report=str(out),verified=True,images=8408,evaluation_jpegs=len(evaluation_files),sha256=sha(out))))
if __name__=='__main__':main()
