import pytest
from codemodder.codemods import DEFAULT_CODEMODS, match_codemods

CODEMODS = {codemod.NAME: codemod for codemod in DEFAULT_CODEMODS}


class TestMatchCodemods:
    def test_no_include_exclude(self):
        assert match_codemods(None, None) == CODEMODS

    @pytest.mark.parametrize(
        "input_str,expected_output",
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
    def test_include(self, input_str, expected_output):
        assert match_codemods(input_str, None) == expected_output

    @pytest.mark.parametrize(
        "input_str,expected_output",
        [
            (
                "secure-random",
                {k: v for (k, v) in CODEMODS.items() if k not in ("secure-random")},
            ),
            (
                "secure-random,url-sandbox",
                {
                    k: v
                    for (k, v) in CODEMODS.items()
                    if k not in ("secure-random", "url-sandbox")
                },
            ),
        ],
    )
    def test_exclude(self, input_str, expected_output):
        assert match_codemods(None, input_str) == expected_output
