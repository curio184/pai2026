"""Freeze one final configuration and all tests before observing its outputs."""
from pathlib import Path
import ast,datetime,hashlib,json

W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2)

def main():
    assert not (W/'runs/control_v11_final').exists()
    assert not list((W/'runs').glob('heldout_round02_*'))
    assert not (W/'probe_round02_english/outputs').exists()
    assert not (W/'probe_control_v11/outputs').exists()
    audit=read(W/'reports/train16_final_checkpoint_completion_audit.json')
    assert audit['passed'] and audit['optimizer_steps']==6000
    assert read(W/'reports/control_v11_contract_checks.json')['passed']
    original=read(W/'protocol/round02_english.json')
    cases=[]
    for i,c in enumerate(original['heldout_cases']):
        for model in (['v1.0','v1.1'] if i%2==0 else ['v1.1','v1.0']):
            cases.append(dict(**c,kind='search',model=model,jitter=True,group='matched_unseen'))
    for profile in ('blue','red','turns','left'):
        cases.append(dict(id='primitive_'+profile,kind='primitive',scene='clear',profile=profile,model='v1.1',group='video_regression'))
    for scene,color in [('clear','blue'),('clear','red'),('fog_light','blue'),('fog_dense','blue'),('dust','blue')]:
        cases.append(dict(id='search_'+scene+'_'+color,kind='search',scene=scene,color=color,model='v1.1',group='video_regression'))
    cases.append(dict(id='known_T3_blue',kind='search',scene='known_swapped',color='blue',model='v1.1',group='known_failure'))
    assert len(cases)==42
    sources=['run_suite_control_v11.py','run_control_v11_final.py','preregister_control_v11_final.py',
             'check_control_v11_contract.py','bounded_wsl.py','bounded_wsl_entry.py']
    for before,after in [('render_probe_round02_english.py','render_probe_control_v11.py'),
                         ('run_probe_round02_english.py','run_probe_control_v11.py'),
                         ('plot_probe_round02_english.py','plot_probe_control_v11.py')]:
        text=(W/'scripts'/before).read_text(encoding='utf-8')
        text=text.replace('selected_final_round02_english.json','selected_control_v11.json')
        text=text.replace('probe_round02_english/','probe_control_v11/')
        text=text.replace('figures_round02_english','figures_control_v11')
        ast.parse(text,filename=after)
        with (W/'scripts'/after).open('x',encoding='utf-8') as f:f.write(text)
        sources.append(after)
    plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              deadline_utc='2026-10-30T13:06:29.263+00:00',candidate='train16_en',
              configuration='control_v11',checkpoint_sha256=audit['final_sha256'],
              old_checkpoint_sha256=read(W/'protocol/plan.json')['protected']['checkpoint_sha256'],
              authorization='v1.1 control change and2.5hour extension explicitly approved; no further tuning or training',
              selection='Single fixed final6000 checkpoint of already started train16; no evaluation of intermediate checkpoints; no further model selection.',
              original_round_protocol_sha256=sha(W/'protocol/round02_english.json'),
              runtime_lock_sha256=sha(W/'protocol/runtime_control_v11_lock.json'),
              contract_checks_sha256=sha(W/'reports/control_v11_contract_checks.json'),
              static_probe_plan_sha256=sha(W/'protocol/static_probe_round02_english.json'),
              scripts={n:sha(W/'scripts'/n) for n in sources},cases=cases,
              passing=dict(unseen_v11_at_least=14,unseen_v11_total=16,per_color_at_least=7,per_color_total=8,
                           per_layout_at_least=3,per_layout_total=4,video_regression=9,known_failure=1,
                           static_correct_directions_at_least=60,static_total=64,static_whole_quartets_at_least=14,static_whole_quartets_total=16),
              physical_criteria='All existing scorers unchanged, including25cm/.08mps/3seconds, initial hover, rotation, person clearance and landing.',
              original_development_suites='Old exposed dev/stress attempts all retained. They are not run again to select another candidate. This new fixed-system confirmation replaces exploratory iteration, not its historical outcomes or scoring.',
              fair_comparison='Both model versions use identical new control code, English prompts, scene, start and sensor seeds. Compare models within this configuration; do not attribute improvement over old-controller v1.0 exclusively to learning.',
              all_outcomes='Run all42 even if performance fails. Infrastructure errors and interrupted attempts remain; no automatic retry. No post-result changes.',
              limitations='One room, two stationary person appearances, fixed supported English stage commands; no arbitrary-language, unknown-room or real-flight claim.',
              no_truth_to_runtime=True,no_video_changes=True,no_publication=True)
    write(W/'protocol/control_v11_final.json',plan)
    write(W/'protocol/selected_control_v11.json',dict(candidate='train16_en',checkpoint_sha256=audit['final_sha256'],
          created_utc=plan['created_utc'],selection=plan['selection'],configuration='control_v11',
          final_protocol_sha256=sha(W/'protocol/control_v11_final.json')))
    print(json.dumps(dict(cases=len(cases),sha256=sha(W/'protocol/control_v11_final.json'),deadline=plan['deadline_utc'],checkpoint=audit['final_sha256'])))

if __name__=='__main__':main()
