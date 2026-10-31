"""Read saved development inputs/actions only; never run a policy or alter trials."""
import bisect, datetime, hashlib, json
from pathlib import Path
import numpy as np

W = Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

suite = W / 'runs/stress_train05_en'
summary = read(suite / 'summary.json')
manifest = read(W / 'data/dataset05_en/manifest.json')
tasks = {variants[2]: i for i, variants in enumerate(manifest['prompt_variants'])}
assert manifest['braking_coefficient'] == .8
rows = []
for outcome in summary['cases']:
    case = outcome['case']
    rec = suite / (case['id'] + '_' + case['model']) / 'record'
    events_path = rec / 'vla_link_events.json'
    events = [e for e in read(events_path) if e.get('event') == 'inference']
    trace = [json.loads(line) for line in (rec / 'trace.jsonl').read_text().splitlines()]
    times = [r['t'] for r in trace]
    groups = {}
    for e in events:
        state = np.asarray(e['estimated_state'], dtype=float)
        task = tasks[e['instruction']]
        idx = min(bisect.bisect_left(times, e['sim_time_capture']), len(trace)-1)
        if idx and abs(times[idx-1]-e['sim_time_capture']) < abs(times[idx]-e['sim_time_capture']): idx -= 1
        phase = trace[idx]['phase']
        chunk = np.asarray(e['action_chunk'], dtype=float)
        mean = chunk[:10].mean(axis=0)
        row = dict(id=e['id'], image_file=e['image_file'], capture_s=e['sim_time_capture'],
                   phase=phase, task=task, estimated_state=state.tolist(),
                   mean_first_10_action=mean.tolist(), first_action=chunk[0].tolist())
        if task in (2,4,5,6) and state[8] > .5:
            brake = -.8 * state[:2]
            norm = np.linalg.norm(brake)
            if norm > .2: brake *= .2 / norm
            row['registered_horizontal_teacher'] = brake.tolist()
            row['horizontal_teacher_error'] = float(np.linalg.norm(mean[:2]-brake))
            row['output_dot_estimated_velocity'] = float(mean[:2] @ state[:2])
        groups.setdefault(phase, []).append(row)
    phases = {}
    for phase, items in groups.items():
        errors = [r for r in items if 'horizontal_teacher_error' in r]
        phases[phase] = dict(images=len(items), start_s=items[0]['capture_s'], end_s=items[-1]['capture_s'])
        if errors:
            phases[phase].update(horizontal_teacher_error_median=float(np.median([r['horizontal_teacher_error'] for r in errors])),
                horizontal_teacher_error_max=max(r['horizontal_teacher_error'] for r in errors),
                same_direction_as_drift=sum(r['output_dot_estimated_velocity'] > 0 for r in errors),
                armed_images=len(errors), largest_errors=sorted(errors,key=lambda r:r['horizontal_teacher_error'],reverse=True)[:3])
    # Distinguish the actual delayed chunk execution from the first-10 summary.
    by_capture = {e['sim_time_capture']:e for e in events}
    for phase in phases:
        executed = []
        for t in trace:
            e = by_capture.get(t.get('model_capture_time'))
            if t['phase'] != phase or t.get('action_source') != 'policy' or e is None: continue
            own = np.asarray(e['estimated_state'],dtype=float)
            if tasks[e['instruction']] not in (2,4,5,6) or own[8] <= .5: continue
            brake = -.8*own[:2];norm=np.linalg.norm(brake)
            if norm > .2: brake *= .2/norm
            action = np.asarray(t['model_action'][:2],dtype=float)
            current = np.asarray(t['estimated_state'][:2],dtype=float)
            executed.append(dict(error=float(np.linalg.norm(action-brake)),
                action=action, capture_own=own[:2], current_own=current,
                index=t['chunk_index'], dot=float(action@current)))
        if executed:
            phases[phase]['actual_execution'] = dict(samples=len(executed),
                median_teacher_error=float(np.median([a['error'] for a in executed])),
                median_action=np.median([a['action'] for a in executed],axis=0).tolist(),
                median_current_velocity=np.median([a['current_own'] for a in executed],axis=0).tolist(),
                chunk_index_min_median_max=np.percentile([a['index'] for a in executed],[0,50,100]).tolist(),
                same_direction_as_current_drift=sum(a['dot']>0 for a in executed))
    score = read(rec / 'search_score.json')
    rows.append(dict(id=case['id'], success=outcome['success'], color=case['color'],
        failure=read(rec/'result.json').get('mission_failure'),
        goal_hold_s=score['physical']['goal_holds'][case['color']]['physical_hold']['duration_s'],
        initial_hover_s=score['physical']['explicit_hover_instruction_hold']['duration_s'],
        phases=phases, events_sha256=sha(events_path)))
out = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    suite='stress_train05_en', completed=len(rows), planned=summary['planned'],
    scope='Postflight diagnostic from already completed development records; no new inference, training or flight.',
    caveat='Mean first 10 predicted actions is a diagnostic, not a reconstruction of all executed commands. Correlation is not unique causal attribution.', cases=rows)
dest = W / 'reports/train05_en_interim_development_diagnostic.json'
dest.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(completed=len(rows),failures=[{k:r[k] for k in ['id','failure','goal_hold_s','initial_hover_s']} for r in rows if not r['success']],report=str(dest)),ensure_ascii=False))
