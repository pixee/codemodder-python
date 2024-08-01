import json

import pytest

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.semgrep.semgrep_nan_injection import SemgrepNanInjection

each_func = pytest.mark.parametrize("func", ["float", "bool", "complex"])


class TestSemgrepNanInjection(BaseSASTCodemodTest):
    codemod = SemgrepNanInjection
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "nan-injection"

    @each_func
    def test_wrap_if_statement(self, tmpdir, func):
        input_code = f"""\
        def home(request):
            uuid = request.POST.get("uuid")
        
            x = {func}(uuid)
            print(x)
        """
        expected_output = f"""\
        def home(request):
            uuid = request.POST.get("uuid")
        
            if uuid.lower() == "nan":
                raise ValueError
            else:
                x = {func}(uuid)
            print(x)
        """

        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "1932"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": region_data_for_func(func),
                                    }
                                }
                            ],
                            "message": {
                                "text": "Found user input going directly into typecast for bool(), float(), or complex(). This allows an attacker to inject Python's not-a-number (NaN) into the typecast. This results in undefind behavior, particularly when doing comparisons. Either cast to a different type, or add a guard checking for all capitalizations of the string 'nan'."
                            },
                            "ruleId": "python.django.security.nan-injection.nan-injection",
                        }
                    ],
                }
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            results=json.dumps(results),
            num_changes=4,
        )


def region_data_for_func(func):
    data = {
        "float": {
            "endColumn": 20,
            "endLine": 4,
            "snippet": {"text": f"    x = {func}(uuid)"},
            "startColumn": 9,
            "startLine": 4,
        },
        "bool": {
            "endColumn": 19,
            "endLine": 4,
            "snippet": {"text": f"    x = {func}(uuid)"},
            "startColumn": 9,
            "startLine": 4,
        },
        "complex": {
            "endColumn": 22,
            "endLine": 4,
            "snippet": {"text": f"    x = {func}(uuid)"},
            "startColumn": 9,
            "startLine": 4,
        },
    }
    return data.get(func)
