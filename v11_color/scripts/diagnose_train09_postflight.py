"""Offline diagnosis of all completed train09 development cases, including primitives."""
import json, hashlib
from pathlib import Path
import numpy as np

W = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def stats(values):
    return np.percentile(values, [0, 50, 100]).tolist()

def main():
    folder = W / 'runs/dev_train09_en'
    summary = read(folder / 'summary.json')
    rows = []
    for outcome in summary['cases']:
        case = outcome['case']
        record = folder / (case['id'] + '_' + case['model']) / 'record'
        trace_path = record / 'trace.jsonl'
        if not trace_path.exists():
            continue
        traces = [json.loads(line) for line in trace_path.read_text(encoding='utf-8').splitlines()]
        phases = {}
        for phase in dict.fromkeys(r['phase'] for r in traces):
            rr = [r for r in traces if r['phase'] == phase and r.get('estimated_state') is not None]
            if not rr:
                continue
            truth = np.asarray([r['truth'] for r in rr])
            state = np.asarray([r['estimated_state'] for r in rr])
            actions = np.asarray([r['model_action'] for r in rr])
            phases[phase] = dict(
                start_s=rr[0]['t'], end_s=rr[-1]['t'],
                physical_height=stats(-truth[:, 3]), estimated_height=stats(state[:, 3]),
                physical_horizontal_speed=stats(np.linalg.norm(truth[:, 4:6], axis=1)),
                estimated_horizontal_speed=stats(np.linalg.norm(state[:, :2], axis=1)),
                physical_vertical_speed=stats(truth[:, 6]),
                estimated_velocity_median=np.median(state[:, :3], axis=0).tolist(),
                model_action_min_median_max=np.percentile(actions, [0, 50, 100], axis=0).tolist(),
                estimated_roll_pitch= np.percentile(state[:, 4:6], [0, 50, 100], axis=0).tolist(),
                estimated_yaw_rate=stats(state[:, 7]),
                armed_fraction=float((state[:, 8] > .5).mean()),
            )
        score_path = record / ('search_score.json' if case['kind'] == 'search' else 'physical_score.json')
        score = read(score_path)
        physical = score.get('physical', score)
        rows.append(dict(
            case=case, success=score['success'], result=read(record / 'result.json'),
            initial_hover=physical['explicit_hover_instruction_hold'],
            rotations=physical['rotations'], target_holds=physical['goal_holds'],
            clearance=physical['minimum_person_clearance_m'], phases=phases,
            trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),
            score_sha256=hashlib.sha256(score_path.read_bytes()).hexdigest(),
        ))
    result = dict(scope='Postflight analysis only. No inference, flight, runtime, scorer, or training changes.',
                  completed=summary['completed'], planned=summary['planned'], cases=rows)
    output = W / 'reports/train09_en_postflight_development_diagnostic.json'
    assert not output.exists(), 'Preserve earlier diagnostic outputs'
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(path=str(output), completed=len(rows), failed=[r['case']['id'] for r in rows if not r['success']])))

if __name__ == '__main__':
    main()
