from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.sonar.sonar_tempfile_mktemp import SonarTempfileMktemp
from core_codemods.tempfile_mktemp import TempfileMktempTransformer


class TestTempfileMktemp(SonarIntegrationTest):
    codemod = SonarTempfileMktemp
    code_path = "tests/samples/tempfile_mktemp.py"
    replacement_lines = [(3, "tempfile.mkstemp()\n")]
    expected_diff = "--- \n+++ \n@@ -1,3 +1,3 @@\n import tempfile\n \n-tempfile.mktemp()\n+tempfile.mkstemp()\n"
    expected_line_change = "3"
    change_description = TempfileMktempTransformer.change_description
