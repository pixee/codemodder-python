import pytest
from tests.codemods.base_codemod_test import BaseCodemodTest
from core_codemods.combine_startswith_endswith import CombineStartswithEndswith

each_func = pytest.mark.parametrize("func", ["startswith", "endswith"])


class TestCombineStartswithEndswith(BaseCodemodTest):
    codemod = CombineStartswithEndswith

    def test_name(self):
        assert self.codemod.name == "combine-startswith-endswith"

    @each_func
    def test_combine(self, tmpdir, func):
        input_code = f"""
        x = "foo"
        x.{func}("foo") or x.{func}("f")
        """
        expected = f"""
        x = "foo"
        x.{func}(("foo", "f"))
        """
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize(
        "code",
        [
            "x.startswith('foo')",
            "x.startswith(('f', 'foo'))",
            "x.startswith('foo') and x.startswith('f')",
            "x.startswith('foo') and x.startswith('f') or True",
            "x.startswith('foo') or x.endswith('f')",
            "x.startswith('foo') or y.startswith('f')",
        ],
    )
    def test_no_change(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        x = "foo"
        x.startswith("foo") or x.startswith("f")
        """
        lines_to_exclude = [3]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
