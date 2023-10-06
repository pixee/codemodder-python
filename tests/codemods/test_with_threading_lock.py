import pytest
from core_codemods.with_threading_lock import WithThreadingLock
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest

each_class = pytest.mark.parametrize(
    "klass",
    [
        "Lock",
        "RLock",
        "Condition",
        "Semaphore",
        "BoundedSemaphore",
    ],
)


class TestWithThreadingLock(BaseSemgrepCodemodTest):
    codemod = WithThreadingLock

    def test_rule_ids(self):
        assert self.codemod.name() == "bad-lock-with-statement"

    @each_class
    def test_import(self, tmpdir, klass):
        input_code = f"""import threading
with threading.{klass}():
    ...
"""
        expected = f"""import threading
lock = threading.{klass}()
with lock:
    ...
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @each_class
    def test_from_import(self, tmpdir, klass):
        input_code = f"""from threading import {klass}
with {klass}():
    ...
"""
        expected = f"""from threading import {klass}
lock = {klass}()
with lock:
    ...
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @each_class
    def test_simple_replacement_with_as(self, tmpdir, klass):
        input_code = f"""import threading
with threading.{klass}() as foo:
    ...
"""
        expected = f"""import threading
lock = threading.{klass}()
with lock as foo:
    ...
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @each_class
    def test_no_effect_sanity_check(self, tmpdir, klass):
        input_code = f"""import threading
with threading.{klass}():
    ...

with threading_lock():
    ...
"""
        expected = f"""import threading
lock = threading.{klass}()
with lock:
    ...

with threading_lock():
    ...
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @each_class
    def test_no_effect_multiple_with_clauses(self, tmpdir, klass):
        """This is currently an unsupported case"""
        input_code = f"""import threading
with threading.{klass}(), foo():
    ...
"""
        self.run_and_assert(tmpdir, input_code, input_code)
