from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.fix_assert_tuple import FixAssertTuple, FixAssertTupleTransform


class TestFixAssertTuple(BaseIntegrationTest):
    codemod = FixAssertTuple
    original_code = """
    assert (1 == 1, 2 == 2)
    """
    replacement_lines = [(1, "assert 1 == 1\n"), (2, "assert 2 == 2\n")]
    expected_diff = "--- \n+++ \n@@ -1 +1,2 @@\n-assert (1 == 1, 2 == 2)\n+assert 1 == 1\n+assert 2 == 2\n"
    expected_line_change = "1"
    change_description = FixAssertTupleTransform.change_description
    num_changes = 2
