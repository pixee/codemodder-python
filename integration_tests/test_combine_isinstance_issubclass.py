from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.combine_isinstance_issubclass import CombineIsinstanceIssubclass


class TestCombineStartswithEndswith(BaseIntegrationTest):
    codemod = CombineIsinstanceIssubclass
    original_code = """
    x = 'foo'
    if isinstance(x, str) or isinstance(x, bytes):
        print("Yes")
    """
    replacement_lines = [(2, "if isinstance(x, (str, bytes)):\n")]

    expected_diff = "--- \n+++ \n@@ -1,3 +1,3 @@\n x = 'foo'\n-if isinstance(x, str) or isinstance(x, bytes):\n+if isinstance(x, (str, bytes)):\n     print(\"Yes\")\n"
    expected_line_change = "2"
    change_description = CombineIsinstanceIssubclass.change_description
