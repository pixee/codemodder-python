from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.remove_unused_imports import RemoveUnusedImports


class TestRemoveUnusedImports(BaseIntegrationTest):
    codemod = RemoveUnusedImports
    original_code = """
    import abc
    from builtins import complex, dict
    
    abc
    complex
    """
    replacement_lines = [(2, """from builtins import complex\n""")]
    expected_diff = "--- \n+++ \n@@ -1,5 +1,5 @@\n import abc\n-from builtins import complex, dict\n+from builtins import complex\n \n abc\n complex\n"
    expected_line_change = 2
    change_description = RemoveUnusedImports.change_description
