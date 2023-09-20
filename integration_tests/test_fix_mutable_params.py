from core_codemods.fix_mutable_params import FixMutableParams
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestFixMutableParams(BaseIntegrationTest):
    codemod = FixMutableParams
    code_path = "tests/samples/mutable_params.py"
    original_code, _ = original_and_expected_from_code_path(code_path, [])
    expected_new_code = """
def foo(x, y=None):
    y = [] if y is None else y
    y.append(x)
    print(y)


def bar(x="hello"):
    print(x)


def baz(x=None, y=None):
    x = {"foo": 42} if x is None else x
    y = set() if y is None else y
    print(x)
    print(y)
""".lstrip()

    expected_diff = '--- \n+++ \n@@ -1,4 +1,5 @@\n-def foo(x, y=[]):\n+def foo(x, y=None):\n+    y = [] if y is None else y\n     y.append(x)\n     print(y)\n \n@@ -7,6 +8,8 @@\n     print(x)\n \n \n-def baz(x={"foo": 42}, y=set()):\n+def baz(x=None, y=None):\n+    x = {"foo": 42} if x is None else x\n+    y = set() if y is None else y\n     print(x)\n     print(y)\n'
    expected_line_change = 1
    num_changes = 2
    change_description = FixMutableParams.CHANGE_DESCRIPTION
