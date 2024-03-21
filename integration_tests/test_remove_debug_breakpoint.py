from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.remove_debug_breakpoint import RemoveDebugBreakpoint


class TestRemoveDebugBreakpoint(BaseIntegrationTest):
    codemod = RemoveDebugBreakpoint
    original_code = """
    print("hello")
    breakpoint()
    print("world")
    """
    expected_new_code = """
    print("hello")
    print("world")
    """
    expected_diff = (
        '--- \n+++ \n@@ -1,3 +1,2 @@\n print("hello")\n-breakpoint()\n print("world")'
    )
    expected_line_change = "2"
    change_description = RemoveDebugBreakpoint.change_description
