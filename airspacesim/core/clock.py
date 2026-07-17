"""Deterministic simulated-time clock owned by the simulation."""


class SimulationClock:
    """Monotonic simulated clock. Knows nothing about wall time.

    Callers decide how many simulated seconds pass per real tick, which is
    what makes accelerated, paused, and batch execution reproducible.
    """

    def __init__(self, start_seconds=0.0):
        self._now_seconds = float(start_seconds)

    @property
    def now_seconds(self):
        return self._now_seconds

    def advance(self, seconds):
        """Advance the clock by non-negative simulated seconds; return new now."""
        step = float(seconds)
        if step < 0:
            raise ValueError(f"Clock cannot move backwards (got {seconds})")
        self._now_seconds += step
        return self._now_seconds
