from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.use_set_literal import UseSetLiteral


class TestUseSetLiteral(BaseIntegrationTest):
    codemod = UseSetLiteral
    original_code = """
    x = set([1, 2, 3])
    y = set([])
    """
    replacement_lines = [(1, "x = {1, 2, 3}\n"), (2, "y = set()\n")]

    expected_diff = """\
--- 
+++ 
@@ -1,2 +1,2 @@
-x = set([1, 2, 3])
-y = set([])
+x = {1, 2, 3}
+y = set()
"""

    expected_line_change = "1"
    num_changes = 2
    change_description = UseSetLiteral.change_description
