"""Describe every completed failed flight and link deterministically selected input images."""
import argparse
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def details(suite):
    folder = W / 'runs' / suite
    summary = read(folder / 'summary.json')
    failures = []
    for outcome in summary['cases']:
        if outcome['success']:
            continue
        case = outcome['case']
        root = folder / (case['id'] + '_' + case['model'])
        record = root / 'record'
        row = dict(case=case, record=root.relative_to(W).as_posix(),
                   error=outcome.get('error'), images={})
        if not (record / 'search_score.json').exists():
            row['note'] = 'No completed search score; inspect the preserved outcome and logs'
            failures.append(row)
            continue
        score = read(record / 'search_score.json')
        physical, result = score['physical'], read(record / 'result.json')
        target = physical['goal_holds'][case['color']]
        row.update(mission_failure=result.get('mission_failure'),
                   failed_checks=[k for k, v in score['checks'].items() if not v],
                   initial_hover_s=physical['explicit_hover_instruction_hold']['duration_s'],
                   target_hold_s=target['physical_hold']['duration_s'],
                   minimum_goal_distance_m=target['minimum_goal_distance_m'],
                   minimum_person_clearance_m=physical['minimum_person_clearance_m'],
                   score_sha256=sha(record / 'search_score.json'))
        inputs = [x for x in read(record / 'vla_link_events.json') if x['event'] == 'inference']
        navigation = [x for x in inputs if 'wearing ' + case['color'] in x['instruction']]
        trace = [json.loads(line) for line in (record / 'trace.jsonl').read_text().splitlines()]
        hover_times = [x['t'] for x in trace if x['phase'] == 'hover']
        hover = ([x for x in inputs if min(hover_times) <= x['sim_time_capture'] <= max(hover_times)]
                 if hover_times else [])
        for phase, selected in [('navigation', navigation), ('initial_hover', hover)]:
            if not selected:
                continue
            for label, item in [('first', selected[0]), ('last', selected[-1])]:
                path = record / 'observations' / item['image_file']
                assert sha(path) == item['image_sha256']
                row['images'][phase + '_' + label] = dict(path=path.relative_to(W).as_posix(),
                    sha256=item['image_sha256'], capture_time=item['sim_time_capture'],
                    instruction=item['instruction'])
        failures.append(row)
    return dict(suite=suite, completed=summary['completed'], planned=summary['planned'],
                successes=summary['successes'], failures=failures,
                selection_rule='All completed failures. First/last model input under requested-color approach instruction and first hover phase, selected by timestamps, not visual quality.',
                scope='Postflight description only; no new policy inference, no changed criteria')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite', required=True)
    args = parser.parse_args()
    report = details(args.suite)
    output = W / 'reports' / (args.suite + '_failure_details.json')
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(suite=args.suite, completed=report['completed'],
                          failures=[x['case']['id'] for x in report['failures']])))


if __name__ == '__main__':
    main()
