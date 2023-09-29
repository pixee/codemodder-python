from core_codemods.with_threading_lock import WithThreadingLock
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest


class TestWithThreadingLock(BaseSemgrepCodemodTest):
    codemod = WithThreadingLock

    def test_rule_ids(self):
        assert self.codemod.name() == "bad-lock-with-statement"

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

    def test_simple_replacement_with_as(self, tmpdir):
        input_code = """import threading
with threading.Lock() as foo:
    ...
"""
        expected = """import threading
lock = threading.Lock()
with lock as foo:
    ...
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_no_effect_sanity_check(self, tmpdir):
        input_code = """import threading
with threading.Lock():
    ...

with threading_lock():
    ...
"""
        expected = """import threading
lock = threading.Lock()
with lock:
    ...

with threading_lock():
    ...
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_no_effect_multiple_with_clauses(self, tmpdir):
        """This is currently an unsupported case"""
        input_code = """import threading
with threading.Lock(), foo():
    ...
"""
        self.run_and_assert(tmpdir, input_code, input_code)
