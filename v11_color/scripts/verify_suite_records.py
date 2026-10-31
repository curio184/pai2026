"""Independently rescore one completed preregistered suite from preserved records."""
import argparse
import json
import tempfile
from pathlib import Path

from verify_records_round02_english import load_scorers, scene_path, verify_one

W = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite', required=True)
    args = parser.parse_args()
    suite = W / 'runs' / args.suite
    plan, summary = read(suite / 'suite_plan.json'), read(suite / 'summary.json')
    assert summary['planned'] == summary['completed'] == len(plan['cases'])
    assert [r['case'] for r in summary['cases']] == plan['cases']
    temporary_base = W / 'verification_tmp'
    temporary_base.mkdir(exist_ok=True)
    scorers, cases = load_scorers(), []
    for outcome in summary['cases']:
        case = outcome['case']
        source = suite / (case['id'] + '_' + case['model']) / 'record'
        with tempfile.TemporaryDirectory(prefix='suite_', dir=temporary_base) as tmp:
            temporary = Path(tmp).resolve()
            assert temporary.is_relative_to(temporary_base.resolve())
            verified = verify_one(source, scene_path(case), case['kind'] == 'search', temporary, scorers)
        assert verified['flight_success'] == outcome['success']
        cases.append(dict(case=case, **verified))
    report = dict(suite=args.suite, records=len(cases),
                  flight_successes=sum(r['flight_success'] for r in cases),
                  evidence_consistent=True, cases=cases,
                  scope='Offline rescoring of every case in the completed suite; originals unchanged')
    output = W / 'reports' / (args.suite + '_all_records_verified.json')
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'cases'}))


if __name__ == '__main__':
    main()
