from codemodder.codemods.with_threading_lock import WithThreadingLock
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest


class TestWithThreadingLock(BaseSemgrepCodemodTest):
    codemod = WithThreadingLock

    def test_rule_ids(self):
        assert self.codemod.RULE_IDS == ["bad-lock-with-statement"]

    def test_import(self, tmpdir):
        input_code = """import threading
with threading.Lock():
    ...
"""
        expected = """import threading
lock = threading.Lock()
with lock:
    ...
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_from_import(self, tmpdir):
        input_code = """from threading import Lock
with Lock():
    ...
"""
        expected = """from threading import Lock
lock = Lock()
with lock:
    ...
"""
        self.run_and_assert(tmpdir, input_code, expected)
