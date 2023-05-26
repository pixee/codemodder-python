import pytest
from codemodder.codemods import CODEMODS, match_codemods, IncludeExcludeConflict


class TestMatchCodemods:
    def test_no_include_exclude(self):
        assert match_codemods(None, None) == CODEMODS

    def test_both_include_exclude(self):
        with pytest.raises(IncludeExcludeConflict):
            match_codemods("secure-random", "url-sandbox")

    @pytest.mark.parametrize(
        "input_str,expexted_output",
        [
            ("secure-random", {"secure-random": CODEMODS["secure-random"]}),
            (
                "secure-random,url-sandbox",
                {
                    "secure-random": CODEMODS["secure-random"],
                    "url-sandbox": CODEMODS["url-sandbox"],
                },
            ),
        ],
    )
    def test_include(self, input_str, expexted_output):
        assert match_codemods(input_str, None) == expexted_output

    @pytest.mark.parametrize(
        "input_str,expexted_output",
        [
            ("secure-random", {"url-sandbox": CODEMODS["url-sandbox"]}),
            ("secure-random,url-sandbox", {}),
        ],
    )
    def test_exclude(self, input_str, expexted_output):
        assert match_codemods(None, input_str) == expexted_output
