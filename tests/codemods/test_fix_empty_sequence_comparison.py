import pytest
from core_codemods.fix_empty_sequence_comparison import FixEmptySequenceComparison
from tests.codemods.base_codemod_test import BaseCodemodTest


class TestFixEmptySequenceComparisonIfStatements(BaseCodemodTest):
    codemod = FixEmptySequenceComparison

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
            x = [1]
            if x != []:
                pass
            """,
                """
            x = [1]
            if x:
                pass
            """,
            ),
            (
                """
            x = [1]
            if [] != x:
                pass
            """,
                """
            x = [1]
            if x:
                pass
            """,
            ),
            (
                """
            x = [1]
            if x == []:
                pass
            """,
                """
            x = [1]
            if not x:
                pass
            """,
            ),
            (
                """
            x = [1]
            if [] == x:
                pass
            """,
                """
            x = [1]
            if not x:
                pass
            """,
            ),
            (
                """
            if [1, 2] == []:
                pass
            """,
                """
            if not [1, 2]:
                pass
            """,
            ),
        ],
    )
    def test_change_list(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)
        assert len(self.file_context.codemod_changes) == 1

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
            x = {1: "one", 2: "two"}
            if x != {}:
                pass
            """,
                """
            x = {1: "one", 2: "two"}
            if x:
                pass
            """,
            ),
            (
                """
            x = {1: "one", 2: "two"}
            if {} != x:
                pass
            """,
                """
            x = {1: "one", 2: "two"}
            if x:
                pass
            """,
            ),
            (
                """
            x = {1: "one", 2: "two"}
            if x == {}:
                pass
            """,
                """
            x = {1: "one", 2: "two"}
            if not x:
                pass
            """,
            ),
            (
                """
            x = {1: "one", 2: "two"}
            if {} == x:
                pass
            """,
                """
            x = {1: "one", 2: "two"}
            if not x:
                pass
            """,
            ),
            (
                """
            if {1: "one", 2: "two"} == {}:
                pass
            """,
                """
            if not {1: "one", 2: "two"}:
                pass
            """,
            ),
        ],
    )
    def test_change_dict(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)
        assert len(self.file_context.codemod_changes) == 1

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
            x = (1, 2, 3)
            if x != ():
                pass
            """,
                """
            x = (1, 2, 3)
            if x:
                pass
            """,
            ),
            (
                """
            x = (1, 2, 3)
            if () != x:
                pass
            """,
                """
            x = (1, 2, 3)
            if x:
                pass
            """,
            ),
            (
                """
            x = (1, 2, 3)
            if x == ():
                pass
            """,
                """
            x = (1, 2, 3)
            if not x:
                pass
            """,
            ),
            (
                """
            x = (1, 2, 3)
            if () == x:
                pass
            """,
                """
            x = (1, 2, 3)
            if not x:
                pass
            """,
            ),
            (
                """
            if (1, 2, 3) == ():
                pass
            """,
                """
            if not (1, 2, 3):
                pass
            """,
            ),
        ],
    )
    def test_change_tuple(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)
        assert len(self.file_context.codemod_changes) == 1

    @pytest.mark.parametrize(
        "code",
        [
            """
            x = [1]
            if x == "hi":
                pass
            """,
            """
            x = [1]
            if x is [1]:
                pass
            """,
        ],
    )
    def test_no_change(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)
        assert len(self.file_context.codemod_changes) == 0


@pytest.mark.xfail(
    reason="Not yet support changing multiple comparisons in a statement"
)
class TestFixEmptySequenceComparisonMultipleStatements(BaseCodemodTest):
    codemod = FixEmptySequenceComparison

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
            x = [1, 2]
            y = [3, 4]
            if x != [] or y == []:
                pass
            """,
                """
            if x or not y:
                pass
            """,
            ),
        ],
    )
    def test_change(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)
        assert len(self.file_context.codemod_changes) == 1


@pytest.mark.xfail(
    reason="Not yet support changing comparisons in assignment statements."
)
class TestFixEmptySequenceComparisonAssignmentStatements(BaseCodemodTest):
    codemod = FixEmptySequenceComparison

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
            x = [1, 2]
            res = x == []
            """,
                """
            x = [1, 2]
            res = not x
            """,
            ),
            (
                """
            x = [1, 2]
            res = x != []
            """,
                """
            x = [1, 2]
            res = bool(x)
            """,
            ),
        ],
    )
    def test_change(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)
        assert len(self.file_context.codemod_changes) == 1
