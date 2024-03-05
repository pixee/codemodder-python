import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.fix_assert_tuple import FixAssertTuple


class TestFixAssertTuple(BaseCodemodTest):
    codemod = FixAssertTuple

    def test_name(self):
        assert self.codemod.name == "fix-assert-tuple"

    @pytest.mark.parametrize(
        "input_code,expected_output,change_count",
        [
            ("""assert (1,)""", """assert 1""", 1),
            (
                """assert ("one", Exception, [])""",
                """\
            assert "one"
            assert Exception
            assert []""",
                3,
            ),
        ],
    )
    def test_change(self, tmpdir, input_code, expected_output, change_count):
        self.run_and_assert(
            tmpdir, input_code, expected_output, num_changes=change_count
        )
        for idx, change in enumerate(self.changeset[0].changes):
            assert change.lineNumber == idx + 1

    def test_change_line_pos(self, tmpdir):
        input_code = """
        print(1)
        assert (1, 2, )
        print(2)
        """
        expected_output = """
        print(1)
        assert 1
        assert 2
        print(2)
        """

        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=2)
        first_assert_line = 3
        for idx, change in enumerate(self.changeset[0].changes):
            assert change.lineNumber == idx + first_assert_line

    def test_change_with_message(self, tmpdir):
        input_code = """
        print(1)
        assert (1, 2, ), "some message"
        print(2)
        """
        expected_output = """
        print(1)
        assert 1, "some message"
        assert 2, "some message"
        print(2)
        """

        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=2)

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

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        assert (1, 2)
        """
        lines_to_exclude = [2]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
