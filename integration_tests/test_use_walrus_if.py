from core_codemods.use_walrus_if import UseWalrusIf
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestUseWalrusIf(BaseIntegrationTest):
    codemod = UseWalrusIf
    code_path = "tests/samples/use_walrus_if.py"
    original_code, _ = original_and_expected_from_code_path(code_path, [])
    expected_new_code = """
if (x := sum([1, 2])) is not None:
    print(x)

if y := max([1, 2]):
    print(y)

z = min([1, 2])
print(z)


def whatever():
    if (b := int("2")) == 10:
        print(b)
""".lstrip()

    expected_diff = '--- \n+++ \n@@ -1,9 +1,7 @@\n-x = sum([1, 2])\n-if x is not None:\n+if (x := sum([1, 2])) is not None:\n     print(x)\n \n-y = max([1, 2])\n-if y:\n+if y := max([1, 2]):\n     print(y)\n \n z = min([1, 2])\n@@ -11,6 +9,5 @@\n \n \n def whatever():\n-    b = int("2")\n-    if b == 10:\n+    if (b := int("2")) == 10:\n         print(b)\n'

    num_changes = 3
    expected_line_change = 1
    change_description = UseWalrusIf.CHANGE_DESCRIPTION
