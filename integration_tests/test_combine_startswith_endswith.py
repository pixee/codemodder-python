from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.combine_startswith_endswith import CombineStartswithEndswith


class TestCombineStartswithEndswith(BaseIntegrationTest):
    codemod = CombineStartswithEndswith
    original_code = """
    x = 'foo'
    if x.startswith("foo") or x.startswith("bar"):
        print("Yes")
    """
    replacement_lines = [(2, 'if x.startswith(("foo", "bar")):\n')]

    expected_diff = '--- \n+++ \n@@ -1,3 +1,3 @@\n x = \'foo\'\n-if x.startswith("foo") or x.startswith("bar"):\n+if x.startswith(("foo", "bar")):\n     print("Yes")\n'
    expected_line_change = "2"
    change_description = CombineStartswithEndswith.change_description
