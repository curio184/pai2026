"""Generate frozen scene assets, then execute final42 and static interventions once."""
import datetime,json,subprocess,sys
from pathlib import Path
from run_suite_rebuild03_final import W,P,PY,BLENDER,sha,write,run_case,lock_check
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def status(stage,**extra):
    obj=dict(stage=stage,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra)
    write(W/'rebuild10h_status.json',obj);print(json.dumps(obj),flush=True)
def command(stage,args,timeout):
    status(stage)
    with (W/'logs'/('rebuild03_final_'+stage+'.log')).open('x',encoding='utf-8') as log:
        r=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
    if r.returncode:raise RuntimeError((stage,r.returncode))
def main():
    plan=read(W/'protocol/rebuild03_final.json')
    assert sha(W/'scripts/run_suite_rebuild03_final.py')==plan['runner_sha256']
    for n,h in plan['source_scripts'].items():assert sha(W/'scripts'/n)==h,n
    root=W/'runs/rebuild03_final';root.mkdir(exist_ok=False)
    write(root/'suite_plan.json',plan)
    old=P/read(W/'protocol/plan.json')['training']['initial_checkpoint'];new=W/'models'/plan['candidate']/'final'
    assert sha(old/'model.safetensors')==plan['old_checkpoint_sha256']
    assert sha(new/'model.safetensors')==plan['checkpoint_sha256']
    assert sha(P/'score_mission.py')==plan['original_physical_scorer_sha256']
    assert sha(P/'civic_render_client.py')==plan['renderer_sha256']
    for version,ck in [('v1.0',old),('v1.1',new)]:
        for name,h in plan['checkpoint_metadata_sha256'][version].items():assert sha(ck/name)==h,name
    command('scene_assets',[BLENDER,'--factory-startup','--background','--python',str(W/'scripts/prepare_scenes_rebuild03.py')],300)
    outcomes=[]
    deadline=datetime.datetime.fromisoformat(plan['deadline_utc'].replace('Z','+00:00'))
    for case in plan['cases']:
        if (deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds()<1800:
            status('deadline_reserve',completed=len(outcomes));return
        lock_check()
        status('final_flight',case=case['id'],model=case['model'],completed=len(outcomes),planned=42)
        outcome=run_case(case,new if case['model']=='v1.1' else old,root/(case['id']+'_'+case['model']));outcomes.append(outcome)
        write(root/'summary.json',dict(cases=outcomes,completed=len(outcomes),planned=42))
        if outcome.get('error'):raise RuntimeError(outcome)
    status('final_flights_complete',completed=42)
    command('static_images',[BLENDER,'--factory-startup','--background','--python',str(W/'scripts/render_probe_rebuild03.py')],300)
    command('static_inference',[str(PY),'-B','-X','utf8',str(W/'scripts/run_probe_rebuild03.py')],600)
    command('static_figures',[sys.executable,'-B','-X','utf8',str(W/'scripts/plot_probe_rebuild03.py')],120)
    status('final_evidence_ready',flights=42)
if __name__=='__main__':
    try:main()
    except BaseException as e:status('final_error',error=repr(e));raise
