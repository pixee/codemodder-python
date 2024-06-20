import mock
import pytest

from codemodder.codemods.test import BaseCodemodTest
from codemodder.dependency import Security
from core_codemods.process_creation_sandbox import ProcessSandbox


@mock.patch("codemodder.codemods.api.FileContext.add_dependency")
class TestProcessCreationSandbox(BaseCodemodTest):
    codemod = ProcessSandbox

    def test_name(self, _):
        assert self.codemod.name == "sandbox-process-creation"

    def test_import_subprocess(self, adds_dependency, tmpdir):
        input_code = """
        import subprocess

        def foo(cmd):
            subprocess.run(cmd, shell=True)
            var = "hello"
        """
        expected = """
        import subprocess
        from security import safe_command

        def foo(cmd):
            safe_command.run(subprocess.run, cmd, shell=True)
            var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    def test_import_alias(self, adds_dependency, tmpdir):
        input_code = """
        import subprocess as sub

        def foo(cmd):
            sub.run(cmd, shell=True)
            var = "hello"
        """
        expected = """
        import subprocess as sub
        from security import safe_command

        def foo(cmd):
            safe_command.run(sub.run, cmd, shell=True)
            var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    def test_from_subprocess(self, adds_dependency, tmpdir):
        input_code = """
        from subprocess import run

        def foo(cmd):
            run(cmd, shell=True)
            var = "hello"
        """
        expected = """
        from subprocess import run
        from security import safe_command

        def foo(cmd):
            safe_command.run(run, cmd, shell=True)
            var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    def test_subprocess_nameerror(self, _, tmpdir):
        input_code = """
        def foo(cmd):
            subprocess.run(cmd, shell=True)

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
                def foo(cmd):
                    subprocess.run(cmd, shell=True)
                    csv.excel
                """,
                """
                import subprocess
                import csv
                from security import safe_command

                def foo(cmd):
                    safe_command.run(subprocess.run, cmd, shell=True)
                    csv.excel
                """,
            ),
            (
                """
                import subprocess
                from csv import excel
                def foo(cmd):
                    subprocess.run(cmd, shell=True)
                    excel
                """,
                """
                import subprocess
                from csv import excel
                from security import safe_command

                def foo(cmd):
                    safe_command.run(subprocess.run, cmd, shell=True)
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

        def foo(cmd, cmd2):
            subprocess.run(cmd, shell=True)
            subprocess.check_output([cmd2, "-l"])"""

        expected = """
        import subprocess
        from security import safe_command

        def foo(cmd, cmd2):
            safe_command.run(subprocess.run, cmd, shell=True)
            subprocess.check_output([cmd2, "-l"])"""

        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    @pytest.mark.parametrize("command", ["run", "Popen"])
    def test_subprocess_imported_cmd(self, adds_dependency, tmpdir, command):
        input_code = f"""
        import subprocess
        from whatever import x

        subprocess.{command}([x, "-l"])
        """
        expected = f"""
        import subprocess
        from whatever import x
        from security import safe_command

        safe_command.run(subprocess.{command}, [x, "-l"])
        """
        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    def test_custom_run(self, _, tmpdir):
        input_code = """
        from app_funcs import run

        def foo(cmd):
            run(cmd, shell=True)
        """
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    def test_subprocess_call(self, adds_dependency, tmpdir):
        input_code = """
        import subprocess

        def foo(cmd):
            subprocess.call([cmd, "-l"])
        """
        expected = """
        import subprocess
        from security import safe_command

        def foo(cmd):
            safe_command.run(subprocess.call, [cmd, "-l"])
        """
        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    def test_subprocess_popen(self, adds_dependency, tmpdir):
        input_code = """
        import subprocess

        def foo(cmd):
            subprocess.Popen([cmd, "-l"])
        """
        expected = """
        import subprocess
        from security import safe_command

        def foo(cmd):
            safe_command.run(subprocess.Popen, [cmd, "-l"])
        """
        self.run_and_assert(tmpdir, input_code, expected)
        adds_dependency.assert_called_once_with(Security)

    def test_hardcoded_string(self, _, tmpdir):
        input_code = (
            expected
        ) = """
        import subprocess

        subprocess.Popen("ls -l", shell=True)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_hardcoded_string_propagation(self, _, tmpdir):
        input_code = (
            expected
        ) = """
        import subprocess

        cmd = "ls -l"
        subprocess.Popen(cmd, shell=True)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_hardcoded_array(self, _, tmpdir):
        input_code = (
            expected
        ) = """
        import subprocess

        subprocess.Popen(["ls", "-l"])
        """
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.xfail(reason="Semgrep doesn't seem to support array propagation")
    def test_hardcoded_array_propagation(self, _, tmpdir):
        input_code = (
            expected
        ) = """
        import subprocess

        cmd = ["ls", "-l"]
        subprocess.Popen(cmd)
        """
        self.run_and_assert(tmpdir, input_code, expected)
