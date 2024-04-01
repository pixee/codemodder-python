from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.fix_assert_tuple import FixAssertTupleTransform
from core_codemods.sonar.sonar_fix_assert_tuple import SonarFixAssertTuple


class TestFixAssertTuple(SonarIntegrationTest):
    codemod = SonarFixAssertTuple
    code_path = "tests/samples/fix_assert_tuple.py"
    replacement_lines = [(1, "assert 1 == 1\n"), (2, "assert 2 == 2\n")]
    expected_diff = "--- \n+++ \n@@ -1 +1,2 @@\n-assert (1 == 1, 2 == 2)\n+assert 1 == 1\n+assert 2 == 2\n"
    expected_line_change = "1"
    change_description = FixAssertTupleTransform.change_description
    num_changes = 2
