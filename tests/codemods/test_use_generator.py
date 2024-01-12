import pytest

from core_codemods.use_generator import UseGenerator
from tests.codemods.base_codemod_test import BaseCodemodTest


class TestUseGenerator(BaseCodemodTest):
    codemod = UseGenerator

    @pytest.mark.parametrize("func", ["any", "all", "sum", "min", "max"])
    def test_list_comprehension(self, tmpdir, func):
        original_code = f"""
        x = {func}([i for i in range(10)])
        """
        new_code = f"""
        x = {func}(i for i in range(10))
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_not_special_builtin(self, tmpdir):
        expected = original_code = """
        x = some([i for i in range(10)])
        """
        self.run_and_assert(tmpdir, original_code, expected)

    def test_not_global_function(self, tmpdir):
        expected = original_code = """
        from foo import any
        x = any([i for i in range(10)])
        """
        self.run_and_assert(tmpdir, original_code, expected)

    def test_exclude_line(self, tmpdir):
        input_code = expected = """\
        x = any([i for i in range(10)])
        """
        lines_to_exclude = [1]
        self.assert_no_change_line_excluded(
            tmpdir, input_code, expected, lines_to_exclude
        )
