"""User-directed language amendment before any train04 training or round-2 test."""
import copy,datetime,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    assert not p.exists();p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    assert not (W/'models/train04').exists() and not (W/'models/train04_en').exists()
    assert not (W/'protocol/selected_final_round02.json').exists()
    assert not list((W/'runs').glob('heldout_round02_*'))
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    prompts=read(W/'data/dataset/manifest.json')['prompt_variants']
    roundplan=copy.deepcopy(read(W/'protocol/round02.json'))
    roundplan.update(created_utc=stamp,initial_candidate='train04_en',prompt_language='English only',
        supersedes_unexecuted_protocol_sha256=sha(W/'protocol/round02.json'),
        user_amendment='User requested English-only instructions before train04 started. Positions, seeds, run counts, success criteria and all controller/scorer behavior are unchanged.',
        controller_and_scoring_unchanged=True,runtime_change_scope='Remove the Japanese suffix from seven stage instruction strings in isolated mission-script copies; no logic or gain changes.')
    roundplan.pop('no_runtime_changes',None)
    roundplan['selection_rule']+=' All new runs use English-only stage prompts.'
    roundplan['final_additional_gates']['static_prompt_group']='runtime_english'
    write(W/'protocol/round02_english.json',roundplan)
    probe=copy.deepcopy(read(W/'protocol/static_probe_round02.json'))
    probe.update(created_utc=stamp,round_protocol_sha256=sha(W/'protocol/round02_english.json'),
        prompts={'runtime_english':[prompts[0][2],prompts[1][2]]},
        supersedes_unexecuted_protocol_sha256=sha(W/'protocol/static_probe_round02.json'),
        inference_gate='Only after selected_final_round02_english.json; no interim-weight or development inference on these fresh views')
    write(W/'protocol/static_probe_round02_english.json',probe)
    transition=copy.deepcopy(read(W/'protocol/static_probe.json'))
    transition.update(created_utc=stamp,purpose='English transition diagnostic on exposed round-1 images; not a fresh final evaluation',
        prompts={'runtime_english':[prompts[0][2],prompts[1][2]]},
        inference_gate='Completed train03 checkpoint only, before further learning',
        used_images='Existing probe/images, unchanged',
        development_gate=dict(correct_goal_minimum=60,outputs=64,whole_quartets_minimum=14,quartets=16),
        primary='Same requested-goal direction criterion as the original probe; all outputs reported')
    write(W/'protocol/english_transition_probe.json',transition)
    plan=copy.deepcopy(read(W/'protocol/train04.json'))
    plan.update(created_utc=stamp,candidate='train04_en',round_protocol_sha256=sha(W/'protocol/round02_english.json'),
        probe_protocol_sha256=sha(W/'protocol/static_probe_round02_english.json'),
        supersedes_unstarted_training_plan_sha256=sha(W/'protocol/train04.json'),
        user_amendment='English-only model instructions. No Japanese-only performance claim is required.',
        additional_start_gate='English transition diagnostic of train03 must meet 60/64 directions and 14/16 whole quartets before this frozen-backbone training recipe is used.',
        runtime_exception='Prompt text only, with byte-diff and AST equivalence after normalizing the seven instruction constants; all other frozen runtime components unchanged.')
    plan['training'].update(output='models/train04_en',prompt_probabilities=[0.,0.,1.],
        prompt_language='English only',data='Same 6408 images and 73712 states; captured-state braking labels from dataset04 recipe. Only English prompt variant is sampled.')
    write(W/'protocol/train04_english.json',plan)
    write(W/'protocol/english_language_amendment.json',dict(created_utc=stamp,user_requested=True,
        superseded_plans=['train04.json','round02.json','static_probe_round02.json'],
        status_of_superseded_plans='Not trained and not evaluated; all files preserved',
        new_training_plan_sha256=sha(W/'protocol/train04_english.json'),new_round_sha256=sha(W/'protocol/round02_english.json'),
        layouts_seeds_counts_and_thresholds_unchanged=True,
        runtime_prompts={name:prompts[t][2] for name,t in [('blue',0),('red',1),('takeoff',2),('land',3),('right',4),('left',5),('hover',6)]}))
    print(json.dumps(dict(training_plan_sha256=sha(W/'protocol/train04_english.json'),round_sha256=sha(W/'protocol/round02_english.json'),prompt_language='English',training_started=False)))
if __name__=='__main__':main()
