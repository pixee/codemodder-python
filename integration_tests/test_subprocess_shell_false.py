from core_codemods.subprocess_shell_false import SubprocessShellFalse
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestSubprocessShellFalse(BaseIntegrationTest):
    codemod = SubprocessShellFalse
    code_path = "tests/samples/subprocess_run.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path, [(1, "subprocess.run(\"echo 'hi'\", shell=False)\n")]
    )
    expected_diff = "--- \n+++ \n@@ -1,2 +1,2 @@\n import subprocess\n-subprocess.run(\"echo 'hi'\", shell=True)\n+subprocess.run(\"echo 'hi'\", shell=False)\n"
    expected_line_change = "2"
    change_description = SubprocessShellFalse.CHANGE_DESCRIPTION
    # expected because output code points to fake file
    allowed_exceptions = (FileNotFoundError,)
