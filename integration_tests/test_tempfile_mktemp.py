from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from core_codemods.tempfile_mktemp import TempfileMktemp


class TestTempfileMktemp(BaseIntegrationTest):
    codemod = TempfileMktemp
    code_path = "tests/samples/tempfile_mktemp.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path, [(2, "tempfile.mkstemp()\n")]
    )
    expected_diff = '--- \n+++ \n@@ -1,4 +1,4 @@\n import tempfile\n \n-tempfile.mktemp()\n+tempfile.mkstemp()\n var = "hello"\n'
    expected_line_change = "3"
    change_description = TempfileMktemp.change_description
