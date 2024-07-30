import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.semgrep.semgrep_nan_injection import SemgrepNanInjection


class TestSemgrepNanInjection(BaseSASTCodemodTest):
    codemod = SemgrepNanInjection
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "nan-injection"

    def test_wrap_if_statement(self, tmpdir):
        input_code = """\
        def home(request):
            uuid = request.POST.get("uuid")
        
            x = float(uuid)
            print(x)
        """
        expected_output = """\
        def home(request):
            uuid = request.POST.get("uuid")
        
            if uuid.lower() == "nan":
                raise ValueError
            else:
                x = float(uuid)
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
                                        "region": {
                                            "endColumn": 20,
                                            "endLine": 4,
                                            "snippet": {"text": "    x = float(uuid)"},
                                            "startColumn": 9,
                                            "startLine": 4,
                                        },
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
