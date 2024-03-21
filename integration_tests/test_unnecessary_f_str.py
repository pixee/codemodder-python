from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.remove_unnecessary_f_str import (
    RemoveUnnecessaryFStr,
    RemoveUnnecessaryFStrTransform,
)


class TestFStr(BaseIntegrationTest):
    codemod = RemoveUnnecessaryFStr
    original_code = """
    bad = f"hello"
    good = f"{2+3}"
    """
    replacement_lines = [(1, 'bad = "hello"\n')]

    expected_diff = '--- \n+++ \n@@ -1,2 +1,2 @@\n-bad = f"hello"\n+bad = "hello"\n good = f"{2+3}"\n'
    expected_line_change = "1"
    change_description = RemoveUnnecessaryFStrTransform.change_description
