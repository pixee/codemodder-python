import json
from core_codemods.sonar.sonar_numpy_nan_equality import SonarNumpyNanEquality
from tests.codemods.base_codemod_test import BaseSASTCodemodTest
from textwrap import dedent


class TestSonarNumpyNanEquality(BaseSASTCodemodTest):
    codemod = SonarNumpyNanEquality
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "numpy-nan-equality-S6725"

    def test_simple(self, tmpdir):
        input_code = """\
        import numpy
        if a == numpy.nan:
            pass
        """
        expected = """\
        import numpy
        if numpy.isnan(a):
            pass
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S6725",
                    "component": f"{tmpdir / 'code.py'}",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 3,
                        "endOffset": 17,
                    },
                }
            ]
        }
        self.run_and_assert(
            tmpdir, dedent(input_code), dedent(expected), results=json.dumps(issues)
        )
