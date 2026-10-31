"""Saved development telemetry only: stationary bias, constraints and power events.

This may read a completed prefix of a live suite. It never reads an unfinished
case, calls a model, changes a score, or supplies truth to a running mission.
"""
import argparse
import datetime
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

W = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(W.parent))
from make_revision_data import rotation


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--suite', default='stress_train15_en')
    args = ap.parse_args()
    assert args.suite.startswith(('stress_', 'dev_'))
    root = W / 'runs' / args.suite
    raw = (root / 'summary.json').read_bytes()
    summary = json.loads(raw)
    n = summary['completed']
    assert n == len(summary['cases']) and n > 0
    stem = args.suite + f'_stationary_snapshot_{n:02d}'
    dest = W / 'reports' / (stem + '.json')
    figdir = W / 'figures' / stem
    assert not dest.exists() and not figdir.exists()
    figdir.mkdir()
    cases = []
    for outcome in summary['cases']:
        case = outcome['case']
        record = root / (case['id'] + '_' + case['model']) / 'record'
        rows = [json.loads(x) for x in (record / 'trace.jsonl').read_text().splitlines()]
        events = read(record / 'events.json')
        power_events = [e for e in events if e.get('event') == 'STATUSTEXT' and
                       any(word in e.get('message', {}).get('text', '').lower()
                           for word in ['battery', 'thrust loss', 'failsafe', 'crash:'])]
        cut = min([e['t'] for e in power_events] + [float('inf')])
        rr = [r for r in rows if r['phase'] == 'hover' and
              r.get('estimated_state') is not None and r['t'] < cut]
        physical = read(record / 'physical_score.json')
        result = read(record / 'result.json')
        row = dict(id=case['id'], success=outcome['success'], record=str(record),
                   trace_sha256=sha(record / 'trace.jsonl'),
                   events_sha256=sha(record / 'events.json'),
                   physical_score_sha256=sha(record / 'physical_score.json'),
                   physical_initial_hover_s=physical['explicit_hover_instruction_hold']['duration_s'],
                   mission_failure=result.get('mission_failure'), power_events=power_events)
        if rr:
            times = np.array([r['t'] for r in rr])
            truth = np.array([r['truth'] for r in rr])
            own = np.array([r['estimated_state'] for r in rr])
            action = np.array([r['model_action'] for r in rr])
            # truth[7:11] is the plant's NED/FRD quaternion, as passed to SITL.
            # Both attitudes therefore use the same convention; no visual-frame
            # Euler angle is compared directly with an autopilot Euler angle.
            matrices = np.array([rotation(t[7:11]) for t in truth])
            true_angles = np.array([[math.atan2(m[2, 1], m[2, 2]),
                                     math.asin(np.clip(-m[2, 0], -1, 1))]
                                    for m in matrices])
            body_frd = np.array([m.T @ t[4:7] for m, t in zip(matrices, truth)])
            body_fl = body_frd[:, :2] * [1., -1.]
            physical_speed = np.linalg.norm(truth[:, 4:6], axis=1)
            estimated_speed = np.linalg.norm(own[:, :2], axis=1)
            late = times >= max(times[0], times[-1] - 10.)
            bias = own[:, 4:6] - true_angles
            row['initial_hover_before_first_power_event'] = dict(
                start_s=float(times[0]), end_s=float(times[-1]),
                last10s_samples=int(late.sum()),
                physical_speed_p0_p50_p100=np.percentile(physical_speed, [0,50,100]).tolist(),
                estimated_speed_p0_p50_p100=np.percentile(estimated_speed, [0,50,100]).tolist(),
                last10s_physical_body_velocity_median=np.median(body_fl[late], axis=0).tolist(),
                last10s_estimated_body_velocity_median=np.median(own[late, :2], axis=0).tolist(),
                last10s_actual_roll_pitch_median=np.median(true_angles[late], axis=0).tolist(),
                last10s_estimated_roll_pitch_median=np.median(own[late, 4:6], axis=0).tolist(),
                last10s_roll_pitch_estimation_error_median=np.median(bias[late], axis=0).tolist(),
                last10s_requested_velocity_median=np.median(action[late, :2], axis=0).tolist())
            if not outcome['success']:
                fig, ax = plt.subplots(3, 1, figsize=(10,8), sharex=True, layout='constrained')
                ax[0].plot(times, physical_speed, label='Physical horizontal speed')
                ax[0].plot(times, estimated_speed, label='Estimated horizontal speed', alpha=.8)
                ax[0].axhline(.08, color='red', ls='--', label='Unchanged score limit')
                ax[0].set_ylabel('Speed [m/s]')
                for k, name in enumerate(['Roll', 'Pitch']):
                    ax[k+1].plot(times, np.rad2deg(true_angles[:,k]), label='Physical '+name)
                    ax[k+1].plot(times, np.rad2deg(own[:,4+k]), label='Estimated '+name)
                    ax[k+1].set_ylabel(name+' [degrees]')
                for a in ax:
                    a.grid(alpha=.2)
                    a.legend(fontsize=8)
                ax[-1].set_xlabel('Simulation time [s]')
                fig.suptitle(case['id']+': initial hover, before first power warning')
                fp = figdir / (case['id']+'.png')
                fig.savefig(fp, dpi=130)
                plt.close(fig)
                row['figure'] = str(fp)
                row['figure_sha256'] = sha(fp)
        cases.append(row)
    report = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        suite=args.suite, completed=n, planned=summary['planned'],
        partial_snapshot=n < summary['planned'], successes=summary['successes'],
        summary_snapshot_sha256=hashlib.sha256(raw).hexdigest(),
        script_sha256=sha(Path(__file__)), cases=cases,
        scope='All cases completed at snapshot time. Saved telemetry only; no model calls or score changes.',
        interval='Initial hover before first battery/thrust/failsafe/crash status. Last-ten-second summaries are diagnostic, not acceptance criteria.',
        interpretation='Attitude-estimation error can leave a sustained translational disturbance in a proportional velocity-to-attitude controller. Correlation here does not establish a unique cause. Model noise, lag, stale packets and other effects remain.',
        next_hypothesis='Inspect whether the existing attitude input can support training-only disturbance compensation, rather than repeatedly increasing delayed velocity braking. No new recipe is registered by this report.')
    dest.write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(dict(report=str(dest), completed=n, figures=str(figdir), sha256=sha(dest))))


if __name__ == '__main__':
    main()
