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
    def test_assignment(self, tmpdir, func):
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

    def test_multiple(self, tmpdir):
        input_code = """\
        def view(request):
            tid = request.POST.get("tid")
            some_list = [1, 2, 3, float('nan')]

            float(tid) in some_list

            z = [1, 2, complex(tid), 3]

            x = [float(tid), 1.0, 2.0]

            return [1, 2, float(tid), 3]
        """
        expected_output = """\
        def view(request):
            tid = request.POST.get("tid")
            some_list = [1, 2, 3, float('nan')]

            if tid.lower() == "nan":
                raise ValueError
            else:
                float(tid) in some_list

            if tid.lower() == "nan":
                raise ValueError
            else:
                z = [1, 2, complex(tid), 3]

            if tid.lower() == "nan":
                raise ValueError
            else:
                x = [float(tid), 1.0, 2.0]

            if tid.lower() == "nan":
                raise ValueError
            else:
                return [1, 2, float(tid), 3]
        """

        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "1fdbd5a"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 15,
                                            "endLine": 5,
                                            "snippet": {
                                                "text": "    float(tid) in some_list"
                                            },
                                            "startColumn": 5,
                                            "startLine": 5,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Found user input going directly into typecast for bool(), float(), or complex(). This allows an attacker to inject Python's not-a-number (NaN) into the typecast. This results in undefind behavior, particularly when doing comparisons. Either cast to a different type, or add a guard checking for all capitalizations of the string 'nan'."
                            },
                            "ruleId": "python.django.security.nan-injection.nan-injection",
                        },
                        {
                            "fingerprints": {"matchBasedId/v1": "1fdbd5a"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 28,
                                            "endLine": 7,
                                            "snippet": {
                                                "text": "    z = [1, 2, complex(tid), 3]"
                                            },
                                            "startColumn": 16,
                                            "startLine": 7,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Found user input going directly into typecast for bool(), float(), or complex(). This allows an attacker to inject Python's not-a-number (NaN) into the typecast. This results in undefind behavior, particularly when doing comparisons. Either cast to a different type, or add a guard checking for all capitalizations of the string 'nan'."
                            },
                            "ruleId": "python.django.security.nan-injection.nan-injection",
                        },
                        {
                            "fingerprints": {"matchBasedId/v1": "1fdbd5a"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 20,
                                            "endLine": 9,
                                            "snippet": {
                                                "text": "    x = [float(tid), 1.0, 2.0]"
                                            },
                                            "startColumn": 10,
                                            "startLine": 9,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Found user input going directly into typecast for bool(), float(), or complex(). This allows an attacker to inject Python's not-a-number (NaN) into the typecast. This results in undefind behavior, particularly when doing comparisons. Either cast to a different type, or add a guard checking for all capitalizations of the string 'nan'."
                            },
                            "ruleId": "python.django.security.nan-injection.nan-injection",
                        },
                        {
                            "fingerprints": {"matchBasedId/v1": "1fdbd5a"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 29,
                                            "endLine": 11,
                                            "snippet": {
                                                "text": "    return [1, 2, float(tid), 3]"
                                            },
                                            "startColumn": 19,
                                            "startLine": 11,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Found user input going directly into typecast for bool(), float(), or complex(). This allows an attacker to inject Python's not-a-number (NaN) into the typecast. This results in undefind behavior, particularly when doing comparisons. Either cast to a different type, or add a guard checking for all capitalizations of the string 'nan'."
                            },
                            "ruleId": "python.django.security.nan-injection.nan-injection",
                        },
                    ],
                }
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            results=json.dumps(results),
            num_changes=16,
        )

    def test_once_nested(self, tmpdir):
        input_code = """\
        def view(request):
            tid = request.POST.get("tid")
            assert bool(float(tid)) + 10.0
        """
        expected_output = """\
        def view(request):
            tid = request.POST.get("tid")
            if tid.lower() == "nan":
                raise ValueError
            else:
                assert bool(float(tid)) + 10.0
        """

        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "asdfg"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 28,
                                            "endLine": 3,
                                            "snippet": {
                                                "text": "    assert bool(float(tid)) + 10.0"
                                            },
                                            "startColumn": 12,
                                            "startLine": 3,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Found user input going directly into typecast for bool(), float(), or complex(). This allows an attacker to inject Python's not-a-number (NaN) into the typecast. This results in undefind behavior, particularly when doing comparisons. Either cast to a different type, or add a guard checking for all capitalizations of the string 'nan'."
                            },
                            "properties": {},
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

    def test_twice_nested(self, tmpdir):
        input_code = """\
        def view(request):
            tid = request.POST.get("tid")
            assert complex(bool(float(tid)))
        """
        expected_output = """\
        def view(request):
            tid = request.POST.get("tid")
            if tid.lower() == "nan":
                raise ValueError
            else:
                assert complex(bool(float(tid)))
        """
        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "q324"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 37,
                                            "endLine": 3,
                                            "snippet": {
                                                "text": "    assert complex(bool(float(tid)))"
                                            },
                                            "startColumn": 12,
                                            "startLine": 3,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Found user input going directly into typecast for bool(), float(), or complex(). This allows an attacker to inject Python's not-a-number (NaN) into the typecast. This results in undefind behavior, particularly when doing comparisons. Either cast to a different type, or add a guard checking for all capitalizations of the string 'nan'."
                            },
                            "properties": {},
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

    def test_direct_source(self, tmpdir):
        input_code = """\
        def view(request):
            uuid = float(request.POST.get("uuid"))
        """
        expected_output = """\
        def view(request):
            if request.POST.get("uuid").lower() == "nan":
                raise ValueError
            else:
                uuid = float(request.POST.get("uuid"))
        """
        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "asdtg"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 43,
                                            "endLine": 2,
                                            "snippet": {
                                                "text": '    uuid = float(request.POST.get("uuid"))'
                                            },
                                            "startColumn": 12,
                                            "startLine": 2,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Found user input going directly into typecast for bool(), float(), or complex(). This allows an attacker to inject Python's not-a-number (NaN) into the typecast. This results in undefind behavior, particularly when doing comparisons. Either cast to a different type, or add a guard checking for all capitalizations of the string 'nan'."
                            },
                            "properties": {},
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

    def test_binop(self, tmpdir):
        input_code = """\
        def view(request):
            tid = request.POST.get("tid")
            float(tid + str(10))
        """
        expected_output = """\
        def view(request):
            tid = request.POST.get("tid")
            if tid + str(10).lower() == "nan":
                raise ValueError
            else:
                float(tid + str(10))
        """
        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "asd2"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 25,
                                            "endLine": 3,
                                            "snippet": {
                                                "text": "    float(tid + str(10))"
                                            },
                                            "startColumn": 5,
                                            "startLine": 3,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Found user input going directly into typecast for bool(), float(), or complex(). This allows an attacker to inject Python's not-a-number (NaN) into the typecast. This results in undefind behavior, particularly when doing comparisons. Either cast to a different type, or add a guard checking for all capitalizations of the string 'nan'."
                            },
                            "properties": {},
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
