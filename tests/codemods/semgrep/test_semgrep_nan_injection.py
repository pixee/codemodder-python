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
                    "tool": {"driver": {"name": "Semgrep OSS"}},
                    "results": [
                        {
                            "guid": "b796b74b-275c-4785-b341-76170b43f6d4",
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
            num_changes=4,
            results=json.dumps(results),
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
        expected_diff_per_change = [
            """\
--- 
+++ 
@@ -2,7 +2,10 @@
     tid = request.POST.get("tid")
     some_list = [1, 2, 3, float('nan')]
 
-    float(tid) in some_list
+    if tid.lower() == "nan":
+        raise ValueError
+    else:
+        float(tid) in some_list
 
     z = [1, 2, complex(tid), 3]
 
""",
            """\
--- 
+++ 
@@ -4,7 +4,10 @@
 
     float(tid) in some_list
 
-    z = [1, 2, complex(tid), 3]
+    if tid.lower() == "nan":
+        raise ValueError
+    else:
+        z = [1, 2, complex(tid), 3]
 
     x = [float(tid), 1.0, 2.0]
 
""",
            """\
--- 
+++ 
@@ -6,6 +6,9 @@
 
     z = [1, 2, complex(tid), 3]
 
-    x = [float(tid), 1.0, 2.0]
+    if tid.lower() == "nan":
+        raise ValueError
+    else:
+        x = [float(tid), 1.0, 2.0]
 
     return [1, 2, float(tid), 3]
""",
            """\
--- 
+++ 
@@ -8,4 +8,7 @@
 
     x = [float(tid), 1.0, 2.0]
 
-    return [1, 2, float(tid), 3]
+    if tid.lower() == "nan":
+        raise ValueError
+    else:
+        return [1, 2, float(tid), 3]
""",
        ]

        results = {
            "runs": [
                {
                    "tool": {"driver": {"name": "Semgrep OSS"}},
                    "results": [
                        {
                            "guid": "6470e0a8-2eeb-4268-8677-f96161207b40",
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
                            "guid": "b3056d9a-1618-40be-bf5e-989278305cf0",
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
                            "guid": "3356587c-dd3a-49e1-baee-0aafc0a91511",
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
                            "guid": "626d3911-ed0b-414d-a2c9-af2245b0baee",
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
            expected_diff_per_change,
            num_changes=4,
            results=json.dumps(results),
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
                    "tool": {"driver": {"name": "Semgrep OSS"}},
                    "results": [
                        {
                            "guid": "60e089cd-472e-489e-a264-cfc6e33e651a",
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
            num_changes=4,
            results=json.dumps(results),
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
                    "tool": {"driver": {"name": "Semgrep OSS"}},
                    "results": [
                        {
                            "guid": "014e3945-144d-4c28-960b-4dd09f2a2b8f",
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
            num_changes=4,
            results=json.dumps(results),
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
                    "tool": {"driver": {"name": "Semgrep OSS"}},
                    "results": [
                        {
                            "guid": "d0540cd9-b999-4756-8392-ca2702e94438",
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
            num_changes=4,
            results=json.dumps(results),
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
                    "tool": {"driver": {"name": "Semgrep OSS"}},
                    "results": [
                        {
                            "guid": "33ffdd04-0f27-475c-8c11-2405e9b77526",
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
            num_changes=4,
            results=json.dumps(results),
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
