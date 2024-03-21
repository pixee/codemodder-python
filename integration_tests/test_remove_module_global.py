from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.remove_module_global import RemoveModuleGlobal


class TestRemoveModuleGlobal(BaseIntegrationTest):
    codemod = RemoveModuleGlobal
    original_code = """
    price = 25
    print("hello")
    global price
    price = 30
    """
    expected_new_code = """
    price = 25
    print("hello")
    price = 30
    """
    expected_diff = '--- \n+++ \n@@ -1,4 +1,3 @@\n price = 25\n print("hello")\n-global price\n price = 30'
    expected_line_change = "3"
    change_description = RemoveModuleGlobal.change_description
