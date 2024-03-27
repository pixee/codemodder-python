from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.remove_future_imports import RemoveFutureImports


class TestRemoveFutureImports(BaseIntegrationTest):
    codemod = RemoveFutureImports
    original_code = """
    from __future__ import absolute_import
    from __future__ import *
    
    print("HEY")
    """
    expected_new_code = """
    from __future__ import annotations

    print("HEY")
    """

    expected_diff = """\
--- 
+++ 
@@ -1,4 +1,3 @@
-from __future__ import absolute_import
-from __future__ import *
+from __future__ import annotations
 
 print("HEY")"""

    num_changes = 2
    expected_line_change = "1"
    change_description = RemoveFutureImports.change_description
