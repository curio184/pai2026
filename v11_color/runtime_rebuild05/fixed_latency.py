"""Deliver each VLA result exactly a fixed simulated latency after its capture.

The simulated camera is rendered by Blender, which is far slower than a real
camera. Running physics in real time would add that rendering time to the
control delay. Instead, one observation is captured at a time, and its result
becomes visible to the controller only when simulated time reaches
capture + latency_s. If rendering and inference have not finished by then,
the caller's physics loop blocks (ArduPilot JSON SITL is lockstep, so the
simulated aircraft and autopilot pause together).

No image, person coordinate, detector output or scorer input is read here.
The VLA output is passed through unchanged.
"""
import time


class FixedLatencyLink:
    def __init__(self, link, latency_s=0.4, wait_timeout_s=120.0):
        if latency_s <= 0:
            raise ValueError("Latency must be positive")
        self.link = link
        self.latency_s = float(latency_s)
        self.wait_timeout_s = float(wait_timeout_s)
        self.pending = None
        self.visible = None
        self.deliveries = []
        self.events = link.events

    def _matching_result(self):
        result = self.link.read()
        if result is None or self.pending is None:
            return None
        if abs(result["sim_time_capture"] - self.pending["t"]) > 1e-9:
            return None
        return result

    def deliver(self, now):
        """Return the packet the controller may use at simulated time ``now``.

        Blocks (wall clock only) when the pending result is due but not ready.
        """
        if self.pending is not None and now >= self.pending["t"] + self.latency_s - 1e-9:
            begin = time.monotonic()
            result = self._matching_result()
            while result is None:
                if self.link.stop.is_set():
                    raise RuntimeError("Camera/VLA link stopped while waiting for a result")
                if time.monotonic() - begin > self.wait_timeout_s:
                    raise TimeoutError("VLA result not ready within wall timeout")
                time.sleep(0.002)
                result = self._matching_result()
            waited = time.monotonic() - begin
            self.visible = result
            self.deliveries.append(dict(id=result["id"], capture_s=self.pending["t"], delivered_s=now,
                                        delivery_age_s=now - self.pending["t"], physics_paused_wall_s=waited,
                                        render_wall_s=result.get("render_wall_s"), inference_s=result.get("inference_s")))
            self.pending = None
        return self.visible

    def capture(self, now, qpos, qvel, estimated_state, instruction):
        """Start the next observation when the previous one has been delivered."""
        if self.pending is None:
            self.link.submit(now, qpos, qvel, estimated_state, instruction)
            self.pending = dict(t=float(now), instruction=instruction)
            return True
        return False

    def close(self):
        self.link.close()
