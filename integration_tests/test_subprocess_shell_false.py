from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.subprocess_shell_false import (
    SubprocessShellFalse,
    SubprocessShellFalseTransformer,
)


class TestSubprocessShellFalse(BaseIntegrationTest):
    codemod = SubprocessShellFalse
    original_code = """
    import subprocess
    subprocess.run(['ls', '-l'], shell=True)
    """
    replacement_lines = [(2, "subprocess.run(['ls', '-l'], shell=False)\n")]

    expected_diff = "--- \n+++ \n@@ -1,2 +1,2 @@\n import subprocess\n-subprocess.run(['ls', '-l'], shell=True)\n+subprocess.run(['ls', '-l'], shell=False)\n"
    expected_line_change = "2"
    change_description = SubprocessShellFalseTransformer.change_description
    # expected because output code points to fake file
    allowed_exceptions = (FileNotFoundError,)
