"""Track stop intent separately from short safety-hover substitutions.

The existing four-second window and .065 m/s command limit are unchanged.
Completion still requires a fresh, matching policy output. During at most .5 s
of stale_hover, remember the last policy request for this window only; NEVER
execute that old request. No image, target coordinate or scorer input is used.
"""
import numpy as np
from flight_progress import StopCommandWindow


class StopIntentWindow:
    def __init__(self):
        self.window=StopCommandWindow()
        self.reset()

    def reset(self):
        self.window.reset()
        self.last_instruction=None
        self.last_policy_command=None
        self.last_policy_time=None
        self.evidence=None

    def update(self, now, command, valid, *, source, instruction):
        if instruction!=self.last_instruction:
            self.reset()
            self.last_instruction=instruction
        fresh=source=='policy'
        request=np.asarray(command,dtype=float)
        if fresh:
            self.last_policy_command=request.copy()
            self.last_policy_time=float(now)
        short_gap=(source=='stale_hover' and self.last_policy_time is not None
                   and 0<=now-self.last_policy_time<=.5)
        if short_gap:
            request=self.last_policy_command.copy()
        usable=fresh or short_gap
        held=self.window.update(now,request,bool(valid and usable))
        self.evidence=dict(source='fresh_policy' if fresh else 'remembered_intent_only' if short_gap else 'invalid',
                           intent_command=request.tolist(),valid_state=bool(valid),
                           elapsed_since_policy_s=None if self.last_policy_time is None else now-self.last_policy_time,
                           completion_requires_fresh_policy=True,
                           old_request_executed=False)
        return bool(held and fresh)
