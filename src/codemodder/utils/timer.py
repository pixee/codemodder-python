import time
from collections import defaultdict
from contextlib import contextmanager

from typing_extensions import Self


class Timer:
    _times: defaultdict

    def __init__(self):
        self._times = defaultdict(float)

    @contextmanager
    def measure(self, name: str):
        start = time.monotonic()
        try:
            yield
        finally:
            end = time.monotonic()
            self._add_time(name, end - start)

    def _add_time(self, name: str, val: float) -> None:
        self._times[name] = self._times.get(name, 0) + val

    def get_time_ms(self, name: str) -> int:
        return int(self._times.get(name, 0) * 1000)

    def aggregate(self, other: Self) -> None:
        for key, val in other._times.items():
            self._add_time(key, val)
