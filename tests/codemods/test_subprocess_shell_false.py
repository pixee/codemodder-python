import pytest
from core_codemods.subprocess_shell_false import SubprocessShellFalse
from tests.codemods.base_codemod_test import BaseCodemodTest

each_func = pytest.mark.parametrize(
    "func", ["check_output", "check_call", "run", "call", "Popen"]
)


class TestSubprocessShellFalse(BaseCodemodTest):
    codemod = SubprocessShellFalse

    def test_name(self):
        assert self.codemod.name == "subprocess-shell-false"

    @each_func
    def test_import(self, tmpdir, func):
        input_code = f"""
        import subprocess
        subprocess.{func}(args, shell=True)
        """
        expexted_output = f"""
        import subprocess
        subprocess.{func}(args, shell=False)
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    @each_func
    def test_from_import(self, tmpdir, func):
        input_code = f"""
        from subprocess import {func}
        {func}(args, shell=True)
        """
        expexted_output = f"""
        from subprocess import {func}
        {func}(args, shell=False)
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    @each_func
    def test_no_shell(self, tmpdir, func):
        input_code = f"""
        import subprocess
        subprocess.{func}(args, timeout=1)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    @each_func
    def test_shell_False(self, tmpdir, func):
        input_code = f"""
        import subprocess
        subprocess.{func}(args, shell=False)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        import subprocess
        subprocess.run(args, shell=True)
        """
        lines_to_exclude = [3]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )

    @each_func
    def test_has_noqa(self, tmpdir, func):
        input_code = (
            expected
        ) = f"""
        import subprocess
        subprocess.{func}(args, shell=True) # noqa: S603
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_different_noqa_message(self, tmpdir):
        input_code = """
        import subprocess
        subprocess.run(args, shell=True) # noqa: S604
        """
        expected = """
        import subprocess
        subprocess.run(args, shell=False) # noqa: S604
        """
        self.run_and_assert(tmpdir, input_code, expected)
