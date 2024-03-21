from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.fix_empty_sequence_comparison import FixEmptySequenceComparison


class TestFixEmptySequenceComparison(BaseIntegrationTest):
    codemod = FixEmptySequenceComparison
    original_code = """
    x = [1]
    if x != []:
        pass
    """
    replacement_lines = [(2, "if x:\n")]

    expected_diff = (
        "--- \n+++ \n@@ -1,3 +1,3 @@\n x = [1]\n-if x != []:\n+if x:\n     pass\n"
    )
    expected_line_change = "2"
    change_description = FixEmptySequenceComparison.change_description
