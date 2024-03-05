import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.str_concat_in_seq_literal import StrConcatInSeqLiteral


class TestList(BaseCodemodTest):
    codemod = StrConcatInSeqLiteral

    def test_no_change(self, tmpdir):
        input_code = """
        good = ["ab", "cd"]
        good = [f"ab", "cd"]
        var = "ab"
        good = [f"{var}", "cd"]
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                bad = ["ab" "cd", "ef", "gh"]
                """,
                """
                bad = ["ab", "cd", "ef", "gh"]
                """,
            ),
            (
                """
                bad = [
                "ab"
                "cd",
                "ef",
                "gh"]
                """,
                """
                bad = [
                "ab",
                "cd",
                "ef",
                "gh"]
                """,
            ),
            (
                """
                bad = [
                    "ab"
                    "cd",
                    "ef",
                    "gh"
                ]
                """,
                """
                bad = [
                    "ab",
                    "cd",
                    "ef",
                    "gh"
                ]
                """,
            ),
        ],
    )
    def test_change(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("final_comma", ["", ","])
    def test_change_multiple(self, tmpdir, final_comma):
        input_code = f"""
        bad = [
            "ab"
            "cd",
            "ef",
            "gh"
            "ij"{final_comma}
        ]
        """
        expected_output = f"""
        bad = [
            "ab",
            "cd",
            "ef",
            "gh",
            "ij"{final_comma}
        ]
        """
        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=2)

    def test_change_all(self, tmpdir):
        input_code = """
        bad = [
            "ab"
            "cd"
            "ef"
            "gh"
            "ij"
        ]
        """
        expected_output = """
        bad = [
            "ab", "cd", "ef", "gh", "ij"
        ]
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        bad = ["ab" "cd" "ef" "gh" "ij"]
        """
        lines_to_exclude = [2]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )


class TestSet(BaseCodemodTest):
    codemod = StrConcatInSeqLiteral

    def test_no_change(self, tmpdir):
        input_code = """
        good = {"ab", "cd"}
        good = {f"ab", "cd"}
        var = "ab"
        good = {f"{var}", "cd"}
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                bad = {"ab" "cd", "ef", "gh"}
                """,
                """
                bad = {"ab", "cd", "ef", "gh"}
                """,
            ),
            (
                """
                bad = {
                "ab"
                "cd",
                "ef",
                "gh"}
                """,
                """
                bad = {
                "ab",
                "cd",
                "ef",
                "gh"}
                """,
            ),
            (
                """
                bad = {
                    "ab"
                    "cd",
                    "ef",
                    "gh"
                }
                """,
                """
                bad = {
                    "ab",
                    "cd",
                    "ef",
                    "gh"
                }
                """,
            ),
        ],
    )
    def test_change(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("final_comma", ["", ","])
    def test_change_multiple(self, tmpdir, final_comma):
        input_code = f"""
        bad = {{
            "ab"
            "cd",
            "ef",
            "gh"
            "ij"{final_comma}
        }}
        """
        expected_output = f"""
        bad = {{
            "ab",
            "cd",
            "ef",
            "gh",
            "ij"{final_comma}
        }}
        """
        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=2)

    def test_change_all(self, tmpdir):
        input_code = """
        bad = {
            "ab"
            "cd"
            "ef"
            "gh"
            "ij"
        }
        """
        expected_output = """
        bad = {
            "ab", "cd", "ef", "gh", "ij"
        }
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        bad = {"ab" "cd" "ef" "gh" "ij"}
        """
        lines_to_exclude = [2]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )


class TestTuple(BaseCodemodTest):
    codemod = StrConcatInSeqLiteral

    def test_no_change(self, tmpdir):
        input_code = """
        good = ("ab", "cd")
        good = (f"ab", "cd")
        var = "ab"
        good = (f"{var}", "cd")
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                bad = ("ab" "cd", "ef", "gh")
                """,
                """
                bad = ("ab", "cd", "ef", "gh")
                """,
            ),
            (
                """
                bad = (
                "ab"
                "cd",
                "ef",
                "gh")
                """,
                """
                bad = (
                "ab",
                "cd",
                "ef",
                "gh")
                """,
            ),
            (
                """
                bad = (
                    "ab"
                    "cd",
                    "ef",
                    "gh"
                )
                """,
                """
                bad = (
                    "ab",
                    "cd",
                    "ef",
                    "gh"
                )
                """,
            ),
        ],
    )
    def test_change(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("final_comma", ["", ","])
    def test_change_multiple(self, tmpdir, final_comma):
        input_code = f"""
        bad = (
            "ab"
            "cd",
            "ef",
            "gh"
            "ij"{final_comma}
        )
        """
        expected_output = f"""
        bad = (
            "ab",
            "cd",
            "ef",
            "gh",
            "ij"{final_comma}
        )
        """
        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=2)

    def test_no_change_tuple_lookalike(self, tmpdir):
        input_code = """
        concat = (
            "ab"
            "cd"
            "ef"
            "gh"
            "ij"
        )
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_change_all(self, tmpdir):
        input_code = """
        bad = (
            "ab"
            "cd"
            "ef"
            "gh"
            "ij",
        )
        """
        expected_output = """
        bad = (
            "ab","cd","ef","gh","ij",
        )
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        bad = ("ab" "cd" "ef" "gh" "ij")
        """
        lines_to_exclude = [2]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
