"""Freeze fresh same-distribution layouts and implementation before any new flight."""
import ast,datetime,hashlib,json
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2)
def main():
    # Finish the already-running old case, without repeating its flight.
    oldroot=W/'runs/control_v11_final';folder=oldroot/'R2H04_v1.0'
    usage=read(folder/'resource_usage.json');assert usage['exit']==0
    m=read(folder/'manifest.json');s=read(folder/'record/search_score.json')
    if not (folder/'outcome.json').exists():
        write(folder/'outcome.json',dict(id=m['case']['id'],model=m['case']['model'],case=m['case'],flight_started=True,
          success=s['success'],record=str(folder/'record'),runner_exit=0,checks=s['checks'],checkpoint_sha256=m['checkpoint_sha256'],
          scheduler_stopped_after_user_authorized_replacement=True,flight_completed_normally=True,scoring_completed_offline=True))
    oldcases=[read(p) for p in sorted(oldroot.glob('*/outcome.json'))]
    assert len(oldcases)==8
    write(oldroot/'batch_closed.json',dict(completed=8,originally_planned=42,cases=oldcases,all_retained=True,
       reason='User authorized a new role division and fixed validation. Batch scheduler stopped; current eighth flight completed normally. Remaining34 not run; no success-rate claim for unrun cases.'))
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();original=read(W/'protocol/round02_english.json')
    rng=np.random.default_rng(2026103019);layouts=[]
    for i in range(4):
        layouts.append(dict(name=f'heldout_navfocus_{i+1:02d}',positions=[[float(rng.uniform(2.65,3.65)),float(rng.uniform(.52,1.1)),0.],
            [float(rng.uniform(2.65,3.65)),float(rng.uniform(-1.1,-.52)),0.]],blue_actor=i%2))
    layoutplan=dict(created_utc=now,layout_seed=2026103019,layout_sampling=original['layout_sampling'],heldout_layouts=layouts,
      reason='The first four original-layout cases informed the role revision. Use fresh unfiltered layouts from the same distribution; no new training or physical threshold change.')
    write(W/'protocol/navfocus_layouts.json',layoutplan)
    cases=[]
    for i,c in enumerate(original['heldout_cases']):
        c=dict(c);c['id']=f'NFH{i+1:02d}';c['scene']=layouts[i//4]['name']
        # Keep the same preregistered start offsets and sensor seeds for paired comparison.
        for model in (['v1.0','v1.1'] if i%2==0 else ['v1.1','v1.0']):cases.append(dict(**c,kind='search',model=model,jitter=True,group='matched_unseen'))
    oldplan=read(W/'protocol/control_v11_final.json');cases+=oldplan['cases'][32:];assert len(cases)==42
    probe=read(W/'protocol/static_probe_round02_english.json');probe['created_utc']=now;probe['purpose']='Fresh unfiltered same-distribution navfocus layouts; raw VLA language and shirt-color interventions'
    for frame in probe['frames']:frame['scene']=layouts[frame['id']//8]['name']
    write(W/'protocol/static_probe_navfocus.json',probe)
    sources=[]
    mappings=[('prepare_scenes_round02_english.py','prepare_scenes_navfocus.py'),('render_probe_control_v11.py','render_probe_navfocus.py'),
              ('run_probe_control_v11.py','run_probe_navfocus.py'),('plot_probe_control_v11.py','plot_probe_navfocus.py'),
              ('run_suite_control_v11.py','run_suite_navfocus.py'),('run_control_v11_final.py','run_navfocus_final.py')]
    for before,after in mappings:
        text=(W/'scripts'/before).read_text(encoding='utf-8')
        for a,b in [('round02_english.json','navfocus_layouts.json'),('static_probe_navfocus_layouts.json','static_probe_navfocus.json'),
                    ('runtime_control_v11','runtime_navfocus'),('selected_control_v11','selected_navfocus'),('probe_control_v11','probe_navfocus'),
                    ('figures_control_v11','figures_navfocus'),('run_suite_control_v11','run_suite_navfocus'),('control_v11_final','navfocus_final'),
                    ('control_v11_','navfocus_'),("configuration='control_v11'","configuration='navfocus'")]:text=text.replace(a,b)
        if before=='run_suite_control_v11.py':
            text=text.replace("scorer=W/'runtime_navfocus/score_search.py' if search else P/'score_mission.py'","scorer=W/'scripts/score_navfocus.py'")
            text=text.replace("[str(PY),str(scorer),str(out/'record'),'--scene',str(xml)]","[str(PY),str(scorer),str(out/'record'),'--scene',str(xml)]+(['--search'] if search else [])")
        ast.parse(text);(W/'scripts'/after).write_text(text,encoding='utf-8');sources.append(after)
    sources+=['score_navfocus.py','prepare_navfocus_validation.py','integrate_navfocus.py','flight_primitives_navfocus.py','bounded_wsl.py','bounded_wsl_entry.py']
    plan=dict(oldplan);plan.update(created_utc=now,configuration='navfocus',cases=cases,runtime_lock_sha256=sha(W/'protocol/runtime_navfocus_lock.json'),
       static_probe_plan_sha256=sha(W/'protocol/static_probe_navfocus.json'),layout_protocol_sha256=sha(W/'protocol/navfocus_layouts.json'),
       authorization='User explicitly authorized role division and new fixed validation after control_v11 failures. VLA retains person choice, approach, deceleration and stop; ordinary control owns planned primitives.',
       physical_criteria='Original physical thresholds preserved. Request provenance is honestly changed to planned primitives, not policy. Original scorer result retained. Fresh VLA stop intent and unchanged four continuous VLA approach channels additionally required.',
       prior_failed_batch='runs/control_v11_final/batch_closed.json',contract_checks_sha256=None,
       scripts={n:sha(W/'scripts'/n) for n in sources},no_more_training=True,no_post_result_configuration_changes=True)
    write(W/'protocol/navfocus_final.json',plan)
    write(W/'protocol/selected_navfocus.json',dict(candidate=plan['candidate'],checkpoint_sha256=plan['checkpoint_sha256'],created_utc=now,configuration='navfocus',selection=plan['selection']))
    print(json.dumps(dict(cases=42,protocol_sha256=sha(W/'protocol/navfocus_final.json'),deadline=plan['deadline_utc'],fresh_layouts=len(layouts))))
if __name__=='__main__':main()
