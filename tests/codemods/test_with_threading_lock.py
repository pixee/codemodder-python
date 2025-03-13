import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.with_threading_lock import WithThreadingLock

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


class TestWithThreadingLock(BaseCodemodTest):
    codemod = WithThreadingLock

    def test_rule_ids(self):
        assert self.codemod.name == "bad-lock-with-statement"

    @each_class
    def test_import(self, tmpdir, klass):
        input_code = f"""import threading
with threading.{klass}():
    ...
"""
        expected = f"""import threading
{klass.lower()} = threading.{klass}()
with {klass.lower()}:
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
{klass.lower()} = {klass}()
with {klass.lower()}:
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
{klass.lower()} = threading.{klass}()
with {klass.lower()} as foo:
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
{klass.lower()} = threading.{klass}()
with {klass.lower()}:
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


class TestThreadingNameResolution(BaseCodemodTest):
    codemod = WithThreadingLock

    @pytest.mark.parametrize(
        "input_code,expected_code,expected_diff_per_change,num_changes",
        [
            (
                """
                from threading import Lock

                lock = 1
                with Lock():
                    ...
                """,
                """
                from threading import Lock

                lock = 1
                lock_1 = Lock()
                with lock_1:
                    ...
                """,
                [],
                1,
            ),
            (
                """
                from threading import Lock
                from something import lock
                with Lock():
                    ...
                """,
                """
                from threading import Lock
                from something import lock
                lock_1 = Lock()
                with lock_1:
                    ...
                """,
                [],
                1,
            ),
            (
                """
                import threading

                lock = 1
                def f(l):
                    with threading.Lock():
                        return [lock_1 for lock_1 in l]
                """,
                """
                import threading

                lock = 1
                def f(l):
                    lock_2 = threading.Lock()
                    with lock_2:
                        return [lock_1 for lock_1 in l]
                """,
                [],
                1,
            ),
            (
                """
                import threading
                with threading.Lock():
                    int("1")
                with threading.Lock():
                    print()
                var = 1
                with threading.Lock():
                    print()
                """,
                """
                import threading
                lock = threading.Lock()
                with lock:
                    int("1")
                lock_1 = threading.Lock()
                with lock_1:
                    print()
                var = 1
                lock_2 = threading.Lock()
                with lock_2:
                    print()
                """,
                [
                    """\
--- 
+++ 
@@ -1,6 +1,7 @@
 
 import threading
-with threading.Lock():
+lock = threading.Lock()
+with lock:
     int("1")
 with threading.Lock():
     print()
""",
                    """\
--- 
+++ 
@@ -2,7 +2,8 @@
 import threading
 with threading.Lock():
     int("1")
-with threading.Lock():
+lock = threading.Lock()
+with lock:
     print()
 var = 1
 with threading.Lock():
""",
                    """\
--- 
+++ 
@@ -5,5 +5,6 @@
 with threading.Lock():
     print()
 var = 1
-with threading.Lock():
+lock = threading.Lock()
+with lock:
     print()
""",
                ],
                3,
            ),
            (
                """
                import threading

                def my_func():
                    lock = "whatever"
                    with threading.Lock():
                        foo()
                """,
                """
                import threading

                def my_func():
                    lock = "whatever"
                    lock_1 = threading.Lock()
                    with lock_1:
                        foo()
                """,
                [],
                1,
            ),
        ],
    )
    def test_name_resolution(
        self, tmpdir, input_code, expected_code, expected_diff_per_change, num_changes
    ):
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_code,
            expected_diff_per_change,
            num_changes=num_changes,
        )
