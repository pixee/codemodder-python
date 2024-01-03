import pytest
import mock

from codemodder.dependency import Security
from core_codemods.process_creation_sandbox import ProcessSandbox
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest


@mock.patch("codemodder.codemods.api.FileContext.add_dependency")
class TestProcessCreationSandbox(BaseSemgrepCodemodTest):
    codemod = ProcessSandbox

    def test_name(self, _):
        assert self.codemod.name == "sandbox-process-creation"

    def test_import_subprocess(self, adds_dependency, tmpdir):
        input_code = """
        import subprocess

        subprocess.run("echo 'hi'", shell=True)
        var = "hello"
        """
        expected = """
        import subprocess
        from security import safe_command

        safe_command.run(subprocess.run, "echo 'hi'", shell=True)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    def test_import_alias(self, adds_dependency, tmpdir):
        input_code = """
        import subprocess as sub

        sub.run("echo 'hi'", shell=True)
        var = "hello"
        """
        expected = """
        import subprocess as sub
        from security import safe_command

        safe_command.run(sub.run, "echo 'hi'", shell=True)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    def test_from_subprocess(self, adds_dependency, tmpdir):
        input_code = """
        from subprocess import run

        run("echo 'hi'", shell=True)
        var = "hello"
        """
        expected = """
        from subprocess import run
        from security import safe_command

        safe_command.run(run, "echo 'hi'", shell=True)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    def test_subprocess_nameerror(self, _, tmpdir):
        input_code = """
        subprocess.run("echo 'hi'", shell=True)

        import subprocess
        """
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize(
        "input_code,expected",
        [
            (
                """
                import subprocess
                import csv
                subprocess.run("echo 'hi'", shell=True)
                csv.excel
                """,
                """
                import subprocess
                import csv
                from security import safe_command

                safe_command.run(subprocess.run, "echo 'hi'", shell=True)
                csv.excel
                """,
            ),
            (
                """
                import subprocess
                from csv import excel
                subprocess.run("echo 'hi'", shell=True)
                excel
                """,
                """
                import subprocess
                from csv import excel
                from security import safe_command

                safe_command.run(subprocess.run, "echo 'hi'", shell=True)
                excel
                """,
            ),
        ],
    )
    def test_other_import_untouched(
        self, adds_dependency, tmpdir, input_code, expected
    ):
        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    def test_multifunctions(self, adds_dependency, tmpdir):
        # Test that subprocess methods that aren't part of the codemod are not changed.
        # If we add the function as one of
        # our codemods, this test would change.
        input_code = """
        import subprocess

        subprocess.run("echo 'hi'", shell=True)
        subprocess.check_output(["ls", "-l"])"""

        expected = """
        import subprocess
        from security import safe_command

        safe_command.run(subprocess.run, "echo 'hi'", shell=True)
        subprocess.check_output(["ls", "-l"])"""

        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    def test_custom_run(self, _, tmpdir):
        input_code = """
        from app_funcs import run

        run("echo 'hi'", shell=True)"""
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    def test_subprocess_call(self, adds_dependency, tmpdir):
        input_code = """
        import subprocess

        subprocess.call(["ls", "-l"])
        """
        expected = """
        import subprocess
        from security import safe_command

        safe_command.run(subprocess.call, ["ls", "-l"])
        """
        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    def test_subprocess_popen(self, adds_dependency, tmpdir):
        input_code = """
        import subprocess

        subprocess.Popen(["ls", "-l"])
        """
        expected = """
        import subprocess
        from security import safe_command

        safe_command.run(subprocess.Popen, ["ls", "-l"])
        """
        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)
