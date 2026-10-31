"""Unintegrated review proposal: bounded horizontal PI velocity control.

No image, language, person coordinates, simulator state or learned parameters.
The caller supplies only a velocity request and estimated aircraft state.
This revision is integrated only into runtime_control_v11; old runtimes are preserved.
"""
from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class Design:
    # For the ideal continuous plant v_dot=a+b, these give
    # s^2 + s + .25 = (s+.5)^2. This is not a proof for the real closed loop.
    proportional: float = 1.0
    integral: float = 0.25
    acceleration_component_limit: float = 0.8
    integral_norm_limit: float = 0.8
    velocity_norm_limit: float = 0.2
    maximum_step_s: float = 0.1


class HorizontalVelocityStabilizer:
    def __init__(self):
        self.design = Design()
        self.integral_ned = np.zeros(2, dtype=np.float64)

    def reset(self):
        self.integral_ned[:] = 0.0

    def update(self, requested_forward_left, estimated_forward_left,
               estimated_yaw_ned, dt, *, armed, stationary_requested):
        """Return attitude requests and an audit record, never motor commands.

        Yaw is absolute estimated NED yaw, not stage-relative yaw. Integral
        compensation stays in a fixed local NED frame across turns.
        stationary_requested is an explicit mission request, not inferred from
        a target's color/location. Both requested and adopted velocities are
        returned so suppressed model outputs cannot be hidden in the log.
        """
        raw = np.asarray(requested_forward_left, dtype=np.float64)
        estimated = np.asarray(estimated_forward_left, dtype=np.float64)
        if raw.shape != (2,) or estimated.shape != (2,):
            self.reset()
            raise ValueError('Expected two horizontal components')
        if not (np.isfinite(raw).all() and np.isfinite(estimated).all()
                and math.isfinite(estimated_yaw_ned) and math.isfinite(dt)):
            self.reset()
            raise ValueError('Invalid estimated state or request; caller must fail safe')
        if not 0 < dt <= self.design.maximum_step_s:
            self.reset()
            raise ValueError('Invalid controller time step')
        desired = raw.copy()
        norm = float(np.linalg.norm(desired))
        if norm > self.design.velocity_norm_limit:
            desired *= self.design.velocity_norm_limit / norm
        if stationary_requested or not armed:
            desired[:] = 0.0
        if not armed:
            self.reset()
            body_acceleration = np.zeros(2)
            rotation = np.eye(2)
        else:
            c, s = math.cos(estimated_yaw_ned), math.sin(estimated_yaw_ned)
            rotation = np.array([[c, -s], [s, c]])  # body FR -> local NE
            error_body = (desired - estimated) * np.array([1.0, -1.0])
            proportional = self.design.proportional * error_body
            integral_body = rotation.T @ self.integral_ned
            increment_body = self.design.integral * error_body * dt
            proposed = proportional + integral_body + increment_body
            limited = np.clip(proposed, -self.design.acceleration_component_limit,
                              self.design.acceleration_component_limit)
            # Conditional integration: do not accumulate in a direction that
            # pushes an already saturated component further into saturation.
            increment_body = np.where(increment_body * (proposed-limited) > 0.0,
                                      0.0, increment_body)
            self.integral_ned += rotation @ increment_body
            magnitude = float(np.linalg.norm(self.integral_ned))
            if magnitude > self.design.integral_norm_limit:
                self.integral_ned *= self.design.integral_norm_limit/magnitude
            body_acceleration = np.clip(proportional + rotation.T @ self.integral_ned,
                                        -self.design.acceleration_component_limit,
                                        self.design.acceleration_component_limit)
        return dict(
            raw_requested_forward_left=raw.tolist(),
            adopted_requested_forward_left=desired.tolist(),
            execution_reason='disarmed' if not armed else 'explicit_stationary_request' if stationary_requested else 'vla_velocity_request',
            acceleration_body_forward_right=body_acceleration.tolist(),
            acceleration_ned=(rotation @ body_acceleration).tolist(),
            integral_ned=self.integral_ned.tolist(),
            roll_rad=math.atan2(float(body_acceleration[1]), 9.81),
            pitch_rad=-math.atan2(float(body_acceleration[0]), 9.81),
            controller_revision="control_v11",
        )
