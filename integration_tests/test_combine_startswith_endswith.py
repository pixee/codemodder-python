from core_codemods.combine_startswith_endswith import CombineStartswithEndswith
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestCombineStartswithEndswith(BaseIntegrationTest):
    codemod = CombineStartswithEndswith
    code_path = "tests/samples/combine_startswith_endswith.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path, [(1, 'if x.startswith(("foo", "bar")):\n')]
    )
    expected_diff = '--- \n+++ \n@@ -1,3 +1,3 @@\n x = \'foo\'\n-if x.startswith("foo") or x.startswith("bar"):\n+if x.startswith(("foo", "bar")):\n     print("Yes")\n'
    expected_line_change = "2"
    change_description = CombineStartswithEndswith.CHANGE_DESCRIPTION
