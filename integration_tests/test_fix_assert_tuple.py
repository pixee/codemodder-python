from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from core_codemods.fix_assert_tuple import FixAssertTuple, FixAssertTupleTransform


class TestFixAssertTuple(BaseIntegrationTest):
    codemod = FixAssertTuple
    code_path = "tests/samples/fix_assert_tuple.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path, [(0, "assert 1 == 1\n"), (1, "assert 2 == 2\n")]
    )
    expected_diff = "--- \n+++ \n@@ -1 +1,2 @@\n-assert (1 == 1, 2 == 2)\n+assert 1 == 1\n+assert 2 == 2\n"
    expected_line_change = "1"
    change_description = FixAssertTupleTransform.change_description
    num_changes = 2
