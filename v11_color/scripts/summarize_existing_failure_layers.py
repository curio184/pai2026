"""Summarize already scored attempts; no rescore, inference or experiments."""
from pathlib import Path
from collections import Counter, defaultdict
import datetime
import hashlib
import json

W=Path(__file__).resolve().parents[1]

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    inventory=W/'results/all_trials_round02_english.json'
    verified=read(W/'reports/train15_en_all_records_verified.json')
    verified_paths={r['record'] for r in verified['cases'] if r['score_matches'] and r['original_unchanged']}
    identities={read(p)['checkpoint_sha256']:p.parent.name for p in (W/'models').glob('*/result.json')}
    groups=defaultdict(list)
    infrastructure=[]
    for r in read(inventory)['all_executed_cases']:
        record=W/r['record']/'record'
        if not (record/'physical_score.json').exists():
            infrastructure.append(r)
            continue
        assert str(record) in verified_paths
        p=read(record/'physical_score.json')
        identity='v1.0' if r['case']['model']=='v1.0' else identities[r['checkpoint_sha256']]
        profile=p['profile']
        flags=[]
        if p['explicit_hover_instruction_hold']['duration_s']<3:flags.append('initial_hover_short')
        if p['minimum_person_clearance_m'] is None or p['minimum_person_clearance_m']<.45:flags.append('person_clearance')
        if not p['takeoff']:flags.append('takeoff')
        if not p['policy_requests']['land']:flags.append('no_policy_landing_request')
        if not p['grounded_disarmed_motors_off']:flags.append('grounded_disarmed_completion')
        if p['watchdog_landing']:flags.append('watchdog_landing')
        goal_hold=None
        if profile in ('blue','red'):
            goal_hold=p['goal_holds'][profile]['physical_hold']['duration_s']
            if goal_hold<3:flags.append('requested_goal_hold_short_or_not_reached')
        else:
            required=['left'] if profile=='left' else ['left','right']
            if not all(p['rotations'][v]['completed'] for v in required):flags.append('primitive_rotation')
        search=record/'search_score.json'
        search_flags=[]
        if search.exists():
            search_flags=[k for k,v in read(search)['checks'].items() if not v and k!='physical_flight']
        row=dict(id=r['case']['id'],record=str(record),checkpoint_sha256=r['checkpoint_sha256'],
                 success=r['success'],profile=profile,requested_goal_hold_s=goal_hold,
                 physical_conditions_not_met=flags,search_conditions_not_met=search_flags,
                 physical_score_sha256=sha(record/'physical_score.json'),
                 mission_failure=r.get('mission_failure'),stop_reason=r.get('stop_reason'))
        groups[(identity,r['suite'])].append(row)
    assert sum(map(len,groups.values()))==verified['records']==287
    output=[]
    for (identity,suite),rows in groups.items():
        output.append(dict(candidate=identity,suite=suite,completed=len(rows),successes=sum(r['success'] for r in rows),
                           physical_failure_flags=dict(Counter(f for r in rows for f in r['physical_conditions_not_met'])),
                           search_failure_flags=dict(Counter(f for r in rows for f in r['search_conditions_not_met'])),
                           cases=rows))
    report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                source_inventory_sha256=sha(inventory),independently_verified_record_count=287,
                candidate_suite_groups=output,infrastructure_records= infrastructure,
                interpretation='Counts are non-exclusive failed conditions, not isolated causes. Failure to reach an approach stage also yields a short goal hold; do not label it a color-choice failure. Different suites/languages/configurations are not pooled as reliability. This is not checkpoint selection.',
                no_new_trials=True,no_score_changes=True,no_inference=True)
    target=W/'reports/existing_failure_layers_all_candidates.json'
    with target.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(output=str(target),sha256=sha(target),records=287,
                          summaries=[{k:v for k,v in r.items() if k!='cases'} for r in output]),ensure_ascii=False))

if __name__=='__main__':
    main()
