"""Assemble the v1.1.0 publication: repository files and the release archive.

Repository (small): code, protocols, summaries, per-flight scores and confirmation images.
Release archive (large): full flight records (trace, VLA outputs, input images) for re-scoring.
Personal local paths are replaced in text files; original and published hashes are recorded.
ArduPilot binary logs, terrain tiles, EEPROM images, model weights and .blend scenes are excluded.
"""
import hashlib,json,re,shutil,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1];SRC=W.parent
REPO=Path(sys.argv[1]);STAGE=Path(sys.argv[2])
OUT=REPO/'v11_color';REL=STAGE/'v11_color'
TEXT={'.py','.json','.md','.txt','.jsonl','.ps1','.cpp','.xml','.csv','.diff','.toml','.cfg','.yaml','.yml','.srt','.log'}
SUBS=[(re.compile(r'(?i)<PROJECT_ROOT>'),'<PROJECT_ROOT>'),
      (re.compile(r'(?i)E:[/\\]+pai2026[/\\]+drone_rescue_stampfly'),'<PROJECT_ROOT>'),
      (re.compile(r'(?i)<WORK_ROOT>'),'<WORK_ROOT>'),(re.compile(r'(?i)E:[/\\]+pai2026'),'<WORK_ROOT>'),
      (re.compile(r'(?i)<NOTES_PATH>"\'\s,]*'),'<NOTES_PATH>'),(re.compile(r'(?i)D:[/\\]+Notes[^"\'\s,]*'),'<NOTES_PATH>'),
      (re.compile(r'(?i)<USER_HOME>'),'<USER_HOME>'),(re.compile(r'(?i)C:[/\\]+Users[/\\]+curio'),'<USER_HOME>'),
      (re.compile(r'//wsl\.localhost/Ubuntu-22\.04<WSL_HOME>'),'<WSL_HOME>'),(re.compile(r'(?i)\\\\+wsl\.localhost\\\\+Ubuntu-22\.04\\\\+home\\\\+curio'),'<WSL_HOME>'),
      (re.compile(r'<WSL_HOME>'),'<WSL_HOME>')]
SKIP_DIRS={'__pycache__','build','logs','terrain'}
SKIP_FILES={'eeprom.bin','renderer.log'}
prov=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def put(src,dst,root_label):
    data=src.read_bytes();out=data
    if src.suffix.lower() in TEXT:
        try:
            t=data.decode('utf-8');u=t
            for rx,rep in SUBS:u=rx.sub(rep,u)
            # Windows-style escaped JSON paths that still mention the local account
            u=re.sub(r'(?i)C:\\\\+Users\\\\+curio','<USER_HOME>',u)
            out=u.encode('utf-8')
        except UnicodeDecodeError:pass
    dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(out)
    prov.append(dict(path=str(dst.relative_to(root_label[0])).replace('\\','/'),source=str(src.relative_to(SRC)).replace('\\','/'),
        source_sha256=sha(data),published_sha256=sha(out),paths_replaced=out!=data,where=root_label[1]))
def tree(src,dst,root,skip_ext=()):
    for f in sorted(src.rglob('*')):
        if f.is_dir() or any(p in SKIP_DIRS for p in f.relative_to(src).parts) or f.name in SKIP_FILES or f.suffix.lower() in skip_ext:continue
        put(f,dst/f.relative_to(src),root)
R=(REPO,'repository');A=(STAGE,'release')
# code and protocols
for d in sorted(W.glob('runtime*')):
    if d.is_dir():tree(d,OUT/d.name,R,skip_ext=('.so','.dll','.o'))
tree(W/'scripts',OUT/'scripts',R)
tree(W/'protocol',OUT/'protocol',R)
tree(W/'results',OUT/'results',R)
for f in sorted(W.glob('ALL_TRIALS*.md')):put(f,OUT/f.name,R)
tree(W/'probe_rebuild05',OUT/'probe_rebuild05',R)
tree(W/'probe_rebuild04',OUT/'probe_rebuild04',R)
# scenes needed for scoring (physics XML and provenance only)
for lay in ['rebuild05_layouts.json','rebuild04_layouts.json']:
    for l in json.loads((W/'protocol'/lay).read_text(encoding='utf-8'))['heldout_layouts']:
        s=W/'scenes'/l['name']
        for rel in ['provenance.json','physics/rescue_scene.xml']:put(s/rel,OUT/'scenes'/l['name']/rel,R)
for name in ['dev01','dev02']:
    put(W/'scenes'/name/'physics/rescue_scene.xml',OUT/'scenes'/name/'physics/rescue_scene.xml',R)
put(SRC/'validation_v1_1/scenes/swapped/physics/rescue_scene.xml',OUT/'scenes/known_swapped/physics/rescue_scene.xml',R)
prim=Path('<WSL_HOME>/physical_ai_ardupilot/realism_bridge_50g_v2/rescue_scene.xml')
data=prim.read_bytes();d=OUT/'scenes/primitive_regression/physics/rescue_scene.xml';d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(data)
prov.append(dict(path='v11_color/scenes/primitive_regression/physics/rescue_scene.xml',source='<WSL_HOME>/physical_ai_ardupilot/realism_bridge_50g_v2/rescue_scene.xml',source_sha256=sha(data),published_sha256=sha(data),paths_replaced=False,where='repository'))
# flight records: small files in the repository, full records in the release archive
SMALL={'manifest.json','outcome.json','command.json','initial_truth_audit.json','summary.json','suite_plan.json','rescored.json'}
SMALL_REC={'result.json','physical_score.json','physical_score_original_contract.json','search_score.json','stages.json','events.json',
           'latency_deliveries.json','discovery.json','notification.json','notification.jpg','search_start_observation.json'}
for group in ['rebuild04_smoke','rebuild04_final','rebuild05_final']:
    g=W/'runs'/group
    for f in sorted(g.rglob('*')):
        if f.is_dir():continue
        rel=f.relative_to(g);parts=rel.parts
        if any(p in SKIP_DIRS for p in parts) or f.name in SKIP_FILES or f.suffix.upper()=='.BIN':continue
        in_record='record' in parts
        if (not in_record and f.name in SMALL) or (in_record and f.name in SMALL_REC and len(parts)<=3):
            put(f,OUT/'runs'/group/rel,R)
        if not f.name.endswith('.log') or f.name in ('runner.log','scoring.log','worker.log'):
            put(f,REL/'runs'/group/rel,A)
# report builder and the figure taken from the video
put(W/'reports/claude_rewrite/build_report.py',OUT/'report/build_report.py',R)
put(W/'reports/claude_rewrite/figures/video_mechanism.png',OUT/'report/figures/video_mechanism.png',R)
pdf=next((SRC/'output/pdf').glob('*再提出版.pdf'))
put(pdf,REPO/'docs/report_v1.1.pdf',R)
(REPO/'v11_color/PUBLICATION_PROVENANCE_v1.1.json').write_text(json.dumps(dict(
    note='Text files had local paths replaced by placeholders (<PROJECT_ROOT>, <USER_HOME>, <WSL_HOME>, <WORK_ROOT>, <NOTES_PATH>). Hashes recorded in protocols refer to the original files; source_sha256 lists them.',
    excluded=['model weights (*.safetensors, *.pt)','Blender scenes (*.blend)','training images and datasets','ArduPilot binary logs, terrain tiles, EEPROM images','renderer logs'],
    files=prov),ensure_ascii=False,indent=1),encoding='utf-8')
print(json.dumps(dict(repository_files=sum(p['where']=='repository' for p in prov),release_files=sum(p['where']=='release' for p in prov),paths_replaced=sum(p['paths_replaced'] for p in prov))))
