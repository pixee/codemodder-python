from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from core_codemods.remove_debug_breakpoint import RemoveDebugBreakpoint


class TestRemoveDebugBreakpoint(BaseIntegrationTest):
    codemod = RemoveDebugBreakpoint
    code_path = "tests/samples/remove_debug_breakpoint.py"
    original_code, _ = original_and_expected_from_code_path(code_path, [])
    expected_new_code = """
print("hello")
print("world")
""".lstrip()
    expected_diff = (
        '--- \n+++ \n@@ -1,3 +1,2 @@\n print("hello")\n-breakpoint()\n print("world")\n'
    )
    expected_line_change = "2"
    change_description = RemoveDebugBreakpoint.change_description
