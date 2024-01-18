from core_codemods.fix_empty_sequence_comparison import FixEmptySequenceComparison
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestFixEmptySequenceComparison(BaseIntegrationTest):
    codemod = FixEmptySequenceComparison
    code_path = "tests/samples/fix_empty_sequence_comparison.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path, [(1, "if x:\n")]
    )
    expected_diff = (
        "--- \n+++ \n@@ -1,3 +1,3 @@\n x = [1]\n-if x != []:\n+if x:\n     pass\n"
    )
    expected_line_change = "2"
    change_description = FixEmptySequenceComparison.change_description
