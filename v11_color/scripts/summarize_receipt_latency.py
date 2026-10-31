"""Postflight timing statistics only; no flight, inference or score changes."""
import datetime
import hashlib
import json
from pathlib import Path
import numpy as np

W = Path(__file__).resolve().parents[1]

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def stats(values):
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    return dict(n=len(a), median=float(np.median(a)), p90=float(np.quantile(a, .9))) if len(a) else dict(n=0)

def main():
    plan = read(W/'protocol/navfocus_receipt.json')
    status = read(W/'receipt_validation_status.json')
    assert status['stage'] == 'flights_complete', status
    roots = sorted((W/'runs/navfocus_receipt').glob('*/outcome.json'))
    assert len(roots) == 42, len(roots)
    rows = []
    sources = {}
    for op in roots:
        outcome = read(op)
        record = op.parent/'record'
        ep, tp = record/'vla_link_events.json', record/'trace.jsonl'
        for p in [op, ep, tp]:
            sources[p.relative_to(W).as_posix()] = sha(p)
        events = [e for e in read(ep) if e['event'] == 'inference']
        captures = [e['sim_time_capture'] for e in events]
        exchange = [e['wall_exchange_s'] for e in events]
        worker = [e['inference_s'] for e in events]
        residual = [e['wall_exchange_s']-e['inference_s'] for e in events]
        ages = []
        with tp.open(encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                if r.get('action_source') == 'policy' and r.get('phase') in ['blue', 'red'] and r.get('model_capture_time') is not None:
                    ages.append(r['t']-r['model_capture_time'])
        rows.append(dict(case=outcome['case'], success=outcome['success'],
            record=record.relative_to(W).as_posix(),
            capture_interval_sim_s=stats(np.diff(captures)),
            exchange_wall_s=stats(exchange), worker_wall_s=stats(worker),
            render_transport_other_wall_s=stats(residual),
            navigation_image_age_at_command_sim_s=stats(ages)))
    for name, h in sources.items():
        assert sha(W/name) == h, name
    out = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope='All 42 preregistered receipt-origin flights, including failures. Offline measurement only.',
        definitions=dict(capture_interval_sim_s='Difference between consecutive capture simulation timestamps.',
            exchange_wall_s='Recorded wall time for image render/transfer and worker response.',
            worker_wall_s='Recorded inference_s; search worker includes SmolVLA plus SSDlite detection; primitive worker differs.',
            render_transport_other_wall_s='exchange_wall_s minus worker_wall_s; not an isolated renderer benchmark.',
            navigation_image_age_at_command_sim_s='Simulation command time minus model capture time on blue/red policy ticks.'),
        limitations=['Wall durations and simulation durations are distinct measurements.',
            'Trace samples overlap and are not independent trials.',
            'This pass changed chunk origin, not update frequency or inference latency.',
            'Timing association does not prove delay was the sole cause of failure.',
            'Maximum speed 0.2m/s is a command bound, not every observed speed. 20cm per second is an illustrative calculation.'],
        cases=rows, source_sha256=sources,
        plan_sha256=sha(W/'protocol/navfocus_receipt.json'))
    dest = W/'reports/receipt_latency_all_trials.json'
    with dest.open('x', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(dict(path=str(dest), cases=len(rows), flight_retries=0)))

if __name__ == '__main__':
    main()
