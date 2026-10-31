"""Own-state instruction progression, independent of scene geometry and scoring."""
from collections import deque

import numpy as np


class StopCommandWindow:
    """Require continuously low own speed and a small mean VLA velocity request.

    The caller supplies validity from estimated state, arming and policy age.
    Commands are time-weighted with zero-order hold, matching their execution.
    A single new noisy sample cannot reset an otherwise physically stable hold.
    This changes progression only; executed commands and scoring are untouched.
    """
    def __init__(self, hold_s=4.0, command_limit_m_s=.065):
        self.hold_s=hold_s
        self.command_limit_m_s=command_limit_m_s
        self.samples=deque()
        self.started=None

    def reset(self):
        self.samples.clear()
        self.started=None

    def update(self, now, command, valid):
        if not valid:
            self.reset()
            return False
        command=np.asarray(command,dtype=float)
        if command.shape!=(2,) or not np.isfinite(command).all():
            self.reset()
            return False
        if self.samples and now<=self.samples[-1][0]:
            raise ValueError("Progress timestamps must increase")
        if self.started is None:self.started=now
        self.samples.append((now,command.copy()))
        cutoff=now-self.hold_s
        while len(self.samples)>1 and self.samples[1][0]<=cutoff:
            self.samples.popleft()
        if now-self.started<=self.hold_s:return False
        integral=np.zeros(2)
        values=list(self.samples)
        for (t,action),(next_t,_) in zip(values,values[1:]):
            integral+=max(0.,next_t-max(t,cutoff))*action
        mean=integral/self.hold_s
        return bool(np.linalg.norm(mean)<self.command_limit_m_s)
