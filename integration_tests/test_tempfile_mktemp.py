from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.tempfile_mktemp import TempfileMktemp, TempfileMktempTransformer


class TestTempfileMktemp(BaseIntegrationTest):
    codemod = TempfileMktemp
    original_code = """
    import tempfile

    tempfile.mktemp()
    var = "hello"
    """
    replacement_lines = [(3, "tempfile.mkstemp()\n")]
    expected_diff = '--- \n+++ \n@@ -1,4 +1,4 @@\n import tempfile\n \n-tempfile.mktemp()\n+tempfile.mkstemp()\n var = "hello"\n'
    expected_line_change = "3"
    change_description = TempfileMktempTransformer.change_description
