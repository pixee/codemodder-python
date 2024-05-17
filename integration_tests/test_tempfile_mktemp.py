from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.tempfile_mktemp import TempfileMktemp, TempfileMktempTransformer


class TestTempfileMktemp(BaseIntegrationTest):
    codemod = TempfileMktemp
    original_code = """
    import tempfile

    filename = tempfile.mktemp()
    """
    replacement_lines = [
        (3, "with tempfile.NamedTemporaryFile(delete=False) as tf:\n"),
        (4, "    filename = tf.name\n"),
    ]
    expected_diff = "--- \n+++ \n@@ -1,3 +1,4 @@\n import tempfile\n \n-filename = tempfile.mktemp()\n+with tempfile.NamedTemporaryFile(delete=False) as tf:\n+    filename = tf.name\n"
    expected_line_change = "3"
    change_description = TempfileMktempTransformer.change_description
