from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from core_codemods.combine_startswith_endswith import CombineStartswithEndswith


class TestCombineStartswithEndswith(BaseIntegrationTest):
    codemod = CombineStartswithEndswith
    code_path = "tests/samples/combine_startswith_endswith.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path, [(1, 'if x.startswith(("foo", "bar")):\n')]
    )
    expected_diff = '--- \n+++ \n@@ -1,3 +1,3 @@\n x = \'foo\'\n-if x.startswith("foo") or x.startswith("bar"):\n+if x.startswith(("foo", "bar")):\n     print("Yes")\n'
    expected_line_change = "2"
    change_description = CombineStartswithEndswith.change_description
