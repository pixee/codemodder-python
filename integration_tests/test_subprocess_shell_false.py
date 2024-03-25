from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.subprocess_shell_false import SubprocessShellFalse


class TestSubprocessShellFalse(BaseIntegrationTest):
    codemod = SubprocessShellFalse
    original_code = """
    import subprocess
    subprocess.run("echo 'hi'", shell=True)
    """
    replacement_lines = [(2, "subprocess.run(\"echo 'hi'\", shell=False)\n")]

    expected_diff = "--- \n+++ \n@@ -1,2 +1,2 @@\n import subprocess\n-subprocess.run(\"echo 'hi'\", shell=True)\n+subprocess.run(\"echo 'hi'\", shell=False)\n"
    expected_line_change = "2"
    change_description = SubprocessShellFalse.change_description
    # expected because output code points to fake file
    allowed_exceptions = (FileNotFoundError,)
