import pytest
from core_codemods.str_concat_in_list import StrConcatInList
from tests.codemods.base_codemod_test import BaseCodemodTest


class TestStrConcatInList(BaseCodemodTest):
    codemod = StrConcatInList

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
            "ab",
            "cd",
            "ef",
            "gh",
            "ij"
        ]
        """
        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=4)

    # def test_exclude_line(self, tmpdir):
    #     input_code = (
    #         expected
    #     ) = """
    #     bad: str = f"bad" + "bad"
    #     """
    #     lines_to_exclude = [2]
    #     self.run_and_assert(
    #         tmpdir,
    #         input_code,
    #         expected,
    #         lines_to_exclude=lines_to_exclude,
    #     )
