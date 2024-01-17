import pytest
from tests.codemods.base_codemod_test import BaseCodemodTest
from core_codemods.fix_assert_tuple import FixAssertTuple


class TestFixAssertTuple(BaseCodemodTest):
    codemod = FixAssertTuple

    def test_name(self):
        assert self.codemod.name() == "fix-assert-tuple"

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """\
            print(1)
            assert (1, 2, )
            print(2)
            """,
                """\
            print(1)
            assert 1
            assert 2
            print(2)
            """,
            ),
            ("""assert (1,)""", """assert 1"""),
            (
                """assert ("one", Exception, [])""",
                """\
            assert "one"
            assert Exception
            assert []""",
            ),
        ],
    )
    def test_change(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)
        # assert len(self.file_context.codemod_changes) == 1

    @pytest.mark.parametrize(
        "code",
        [
            "assert [1]",
            "assert 1",
            "assert ()",
            "assert (1)",
            "assert ('hi')",
        ],
    )
    def test_no_change(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)
        assert len(self.file_context.codemod_changes) == 0

    def test_exclude_line(self, tmpdir):
        input_code = expected = """\
        assert (1, 2)
        """
        lines_to_exclude = [1]
        self.assert_no_change_line_excluded(
            tmpdir, input_code, expected, lines_to_exclude
        )
