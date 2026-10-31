"""Read-only evidence audit for the full deliverable; does not change gates."""
import datetime,hashlib,json,subprocess
from pathlib import Path
W=Path(__file__).resolve().parents[1];P=W.parent;R=P.parent/'repository'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
rows=[]
def item(name,passed,evidence,detail=None):rows.append(dict(requirement=name,status='verified' if passed else 'incomplete',evidence=str(evidence),detail=detail))
protected={
 'original_model':('outputs/smolvla_training_realism_precision_02/final/model.safetensors','d119adc57fa0c4681f4413b621d6321d27b000c6a3550c5b075bbbebc3d9a467'),
 'original_video':('output/video/rescue_drone_final_quad.mp4','9669ae47300089f327ac347f9e07efcd6c9e02c05cb7ef91212f779af404ed51'),
 'original_pdf':('output/pdf/説明資料_PAI最終課題_最終版.pdf','7bf86e3ab13bc47b0a0f994698bc0d0c1d920648facbacf7ba5f9e16d4c80119')}
for name,(path,expected) in protected.items():
 f=P/path;actual=sha(f) if f.exists() else None;item(name+'_preserved',actual==expected,f,dict(actual_sha256=actual,expected_sha256=expected))
selection=W/'protocol/selected_final_round02_english.json';s=read(selection) if selection.exists() else None
item('final_candidate_selected_after_development_gates',s is not None,selection)
if s:
 result=W/'models'/s['candidate']/'result.json';r=read(result);model=W/'models'/s['candidate']/'final/model.safetensors'
 start=read(W/'models'/s['candidate']/'started.json')
 saved_path=W/'reports'/(s['candidate']+'_saved_training_verification.json');saved=read(saved_path) if saved_path.exists() else {}
 item('selected_weights_are_final_step',r['checkpoint']=='final' and r['optimizer_steps_completed']==start['config']['steps']==saved.get('final_step') and saved.get('passed') is True and r['checkpoint_sha256']==saved.get('checkpoint_sha256')==s['checkpoint_sha256']==sha(model),result)
 if r.get('resumed'):
  resume_path=W/'reports'/(s['candidate'].replace('_en','')+'_resume01_completion_audit.json');resume=read(resume_path) if resume_path.exists() else {}
  item('resumed_training_final_state_verified',resume.get('passed') is True and resume.get('checkpoint_sha256')==s['checkpoint_sha256'] and resume.get('final_step')==r['optimizer_steps_completed'],resume_path)
 if s['candidate'] in ['train14_en','train15_en','train16_en']:
  final_path=W/'reports'/(s['candidate'].replace('_en','')+'_final_checkpoint_completion_audit.json');final_check=read(final_path) if final_path.exists() else {}
  item('final_optimizer_snapshot_matches_saved_model',final_check.get('passed') is True and final_check.get('final_sha256')==s['checkpoint_sha256'] and final_check.get('optimizer_steps')==r['optimizer_steps_completed'],final_path)
aggregate=W/'results/all_trials_round02_english.json';a=read(aggregate) if aggregate.exists() else {}
visibility_path=W/('reports/v11_training_visibility_'+s['candidate'].replace('_en','')+'.json' if s and s['candidate'] in ['train14_en','train15_en','train16_en'] else 'reports/v11_training_visibility_scope.json')
visibility=read(visibility_path) if visibility_path.exists() else {}
selected_started=read(W/'models'/s['candidate']/'started.json') if s else {}
item('adaptation_image_visibility_provenance_verified',bool(s and visibility.get('verified') and visibility.get('dataset_audit_sha256')==selected_started.get('dataset_audit_sha256')),visibility_path)
current=bool(s and a.get('candidate')==s['candidate'] and a.get('selected_checkpoint_sha256')==s['checkpoint_sha256'])
for name,key in [('unseen_placements_repeated_matched_flights','closed_loop_gate_met'),('all_video_scenarios','regression_gate_met'),('color_and_language_interventions','color_intervention_gate_met'),('original_swapped_failure_retested','known_failure_retest_passed'),('all_successes_and_failures_rescored','all_records_independently_rescored'),('actual_runtime_English_prompts_verified','actual_english_instructions_verified'),('probe_arithmetic_and_images_verified','probe_arithmetic_and_images_verified'),('all_preregistered_experiment_gates','preregistered_goal_met')]:
 item(name,current and a.get(key) is True,aggregate,dict(candidate=a.get('candidate'),gate=a.get(key)))
pdfcheck=W/'reports/pdf_check.json';pdf=W/'reports/output/pdf/説明資料_PAI最終課題_v1.1_検証更新版.pdf'
q=read(pdfcheck) if pdfcheck.exists() else {}
item('four_page_pdf_rendered_and_visually_reviewed',bool(s and pdf.exists() and q.get('pages')==4 and q.get('visually_reviewed') is True and q.get('pdf_sha256')==sha(pdf) and q.get('selected_checkpoint_sha256')==s['checkpoint_sha256']),pdfcheck)
publication=W/'reports/publication_checks.json';v=read(publication) if publication.exists() else {}
candidate=Path(v['candidate']) if v.get('candidate') else None
item('README_and_evidence_review_copy_verified',bool(candidate and (candidate/'README.md').exists() and (candidate/'DISTRIBUTION_MANIFEST.json').exists() and v.get('all_additional_records_verified') and v.get('provenance_verified')),publication,'Link and replay audit must be rerun after any candidate changes.')
git=subprocess.run(['git','-C',str(R),'status','--porcelain'],capture_output=True,text=True,check=True)
head=subprocess.run(['git','-C',str(R),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
item('public_checkout_not_modified_without_approval',not git.stdout.strip() and head=='a4e5f01b51591b9cd32c5bc7cc3cde2d818fe83a',R,dict(head=head,clean=not git.stdout.strip()))
now=datetime.datetime.now(datetime.timezone.utc);dest=W/'reports/delivery_audits';dest.mkdir(exist_ok=True)
report=dict(created_utc=now.isoformat(),scope='Evidence existence, content hashes and gate checks. Not a substitute for final human-readable claim-to-evidence review or PDF visual review.',requirements=rows,all_machine_checks_pass=all(r['status']=='verified' for r in rows),manual_review_still_required=['PDF and README claims match the actual scope and results','All original user requirements accounted for','No publish/tag/resubmit without user approval'])
out=dest/(now.strftime('%Y%m%dT%H%M%S')+'.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(report=str(out),verified=sum(r['status']=='verified' for r in rows),requirements=len(rows),incomplete=[r['requirement'] for r in rows if r['status']!='verified'])))
