from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from core_codemods.remove_module_global import RemoveModuleGlobal


class TestRemoveModuleGlobal(BaseIntegrationTest):
    codemod = RemoveModuleGlobal
    code_path = "tests/samples/module_global.py"
    original_code, _ = original_and_expected_from_code_path(code_path, [])
    expected_new_code = """
price = 25
print("hello")
price = 30
""".lstrip()
    expected_diff = '--- \n+++ \n@@ -1,4 +1,3 @@\n price = 25\n print("hello")\n-global price\n price = 30\n'
    expected_line_change = "3"
    change_description = RemoveModuleGlobal.change_description
