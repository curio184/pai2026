"""Run exactly the registered linear diagnostic grid, not a simulator flight."""
import datetime
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np

W = Path(__file__).resolve().parents[1]
plan_path = W/'protocol/stationary_feedback_analysis01.json'
plan_bytes = plan_path.read_bytes()
plan = json.loads(plan_bytes)
out = W/'reports/stationary_feedback_analysis01.json'
trajectories = W/'reports/stationary_feedback_analysis01_trajectories.npz'
assert not out.exists() and not trajectories.exists()
dt = plan['integration_step_s']
times = np.arange(round(plan['duration_s']/dt)+1)*dt
rows = []
signals = []
for method, disturbance, initial, period, delay, lag in itertools.product(
        plan['methods'], plan['disturbances_m_s2'], plan['initial_velocities_m_s'],
        plan['capture_periods_s'], plan['delivery_delays_s'], plan['attitude_lags_s']):
    v = initial
    accel = plan['initial_estimated_acceleration_m_s2']
    request = 0.
    pending = {}
    capture_every = round(period/dt)
    delay_steps = round(delay/dt)
    trace = []
    for step, t in enumerate(times):
        if step % capture_every == 0:
            if method == 'velocity_only_mild': candidate = -.6*v
            elif method == 'velocity_only_strong': candidate = -1.6*v
            elif method == 'attitude_incremental': candidate = .75*v + accel
            else: raise ValueError(method)
            pending[step+delay_steps] = float(np.clip(candidate, -.2, .2))
        if step in pending:
            request = pending.pop(step)
        trace.append([v, accel, request])
        # Simultaneous explicit Euler, dt is at most 1/20 smallest lag.
        v, accel = v+dt*(accel+disturbance), accel+dt*(request-v-accel)/lag
    trace = np.asarray(trace, dtype=np.float32)
    assert np.isfinite(trace).all()
    tail = trace[times >= times[-1]-10, 0]
    rows.append(dict(index=len(rows), method=method, disturbance_m_s2=disturbance,
        initial_velocity_m_s=initial, capture_period_s=period, delivery_delay_s=delay,
        attitude_lag_s=lag, last10_speed_rms_m_s=float(np.sqrt(np.mean(tail**2))),
        last10_speed_max_m_s=float(np.abs(tail).max()),
        max_request_m_s=float(np.abs(trace[:,2]).max())))
    signals.append(trace)
np.savez_compressed(trajectories, time_s=times, signals=np.stack(signals))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
aggregates = []
for method in plan['methods']:
    cases = [r for r in rows if r['method'] == method]
    aggregates.append(dict(method=method, cases=len(cases),
        median_last10_speed_rms_m_s=float(np.median([r['last10_speed_rms_m_s'] for r in cases])),
        worst_last10_speed_max_m_s=max(r['last10_speed_max_m_s'] for r in cases)))
result = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    plan_sha256=hashlib.sha256(plan_bytes).hexdigest(), script_sha256=sha(Path(__file__)),
    scope=plan['scope'], limitations=plan['limitations'], cases=rows, aggregates=aggregates,
    trajectories=str(trajectories), trajectories_sha256=sha(trajectories),
    axes=['case', 'time', 'velocity/estimated_acceleration/delivered_request'])
out.write_text(json.dumps(result, indent=2), encoding='utf8')
print(json.dumps(dict(report=str(out), cases=len(rows), aggregates=aggregates, sha256=sha(out))))
