import json
from core_codemods.sonar.sonar_remove_assertion_in_pytest_raises import (
    SonarRemoveAssertionInPytestRaises,
)
from tests.codemods.base_codemod_test import BaseSASTCodemodTest


class TestRemoveAssertionInPytestRaises(BaseSASTCodemodTest):
    codemod = SonarRemoveAssertionInPytestRaises
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "remove-assertion-in-pytest-raises-S5915"

    def test_simple(self, tmpdir):
        input_code = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
                assert True
        """
        expected = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
            assert True
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S5915",
                    "status": "OPEN",
                    "component": f"{tmpdir / 'code.py'}",
                    "textRange": {
                        "startLine": 6,
                        "endLine": 6,
                        "startOffset": 8,
                        "endOffset": 19,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
