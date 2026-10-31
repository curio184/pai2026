"""Training-only stationary requests using the existing velocity/attitude inputs.

The attitude term is a leaky proxy for the preceding acceleration request. It
does not identify true attitude bias. All runtime control and navigation labels
remain unchanged; actual closed-loop improvement must be tested separately.
"""
import numpy as np
from teacher_flight15 import teacher_chunk as previous_teacher

VELOCITY_RETENTION = .6
ATTITUDE_RETENTION = .9
GRAVITY = 9.81


def stationary_request(own, task):
    s = np.asarray(own, dtype=float)
    if s[8] <= .5 or (task == 2 and s[3] < .25):
        return np.zeros(2)
    # Autopilot FRD roll/pitch; VLA horizontal requests are forward/left.
    acceleration_proxy = -GRAVITY * np.tan(s[[5, 4]])
    request = VELOCITY_RETENTION*s[:2] + ATTITUDE_RETENTION*acceleration_proxy
    norm = np.linalg.norm(request)
    if norm > .2:
        request *= .2/norm
    return request


def teacher_chunk(task, qpos, own, targets, rotation, scale, steps=32):
    chunk = previous_teacher(task, qpos, own, targets, rotation, scale, steps)
    if task in [2, 4, 5, 6]:
        chunk[:, :2] = stationary_request(own, task)/np.asarray(scale[:2])
    return chunk
