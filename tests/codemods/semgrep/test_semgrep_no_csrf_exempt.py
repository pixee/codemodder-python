import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.semgrep.semgrep_no_csrf_exempt import SemgrepNoCsrfExempt


class TestSemgrepNoCsrfExempt(BaseSASTCodemodTest):
    codemod = SemgrepNoCsrfExempt
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "no-csrf-exempt"

    def test_decorators(self, tmpdir):
        input_code = """\
        from django.http import JsonResponse
        from django.views.decorators.csrf import csrf_exempt
        from django.dispatch import receiver
        from django.core.signals import request_finished
        
        @csrf_exempt
        def ssrf_code_checker(request):
            if request.user.is_authenticated:
                if request.method == 'POST':
                    return JsonResponse({'message': 'Testbench failed'}, status=200)
            return JsonResponse({'message': 'UnAuthenticated User'}, status=401)
        
        
        @receiver(request_finished)
        @csrf_exempt
        def foo():
            pass
        """
        expected_output = """\
        from django.http import JsonResponse
        from django.views.decorators.csrf import csrf_exempt
        from django.dispatch import receiver
        from django.core.signals import request_finished
        
        def ssrf_code_checker(request):
            if request.user.is_authenticated:
                if request.method == 'POST':
                    return JsonResponse({'message': 'Testbench failed'}, status=200)
            return JsonResponse({'message': 'UnAuthenticated User'}, status=401)
        
        
        @receiver(request_finished)
        def foo():
            pass
        """

        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "a3ca2"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 73,
                                            "endLine": 11,
                                            "snippet": {
                                                "text": "@csrf_exempt\ndef ssrf_code_checker(request):\n    if request.user.is_authenticated:\n        if request.method == 'POST':\n            return JsonResponse({'message': 'Testbench failed'}, status=200)\n    return JsonResponse({'message': 'UnAuthenticated User'}, status=401)"
                                            },
                                            "startColumn": 1,
                                            "startLine": 6,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Detected usage of @csrf_exempt, which indicates that there is no CSRF token set for this route. This could lead to an attacker manipulating the user's account and exfiltration of private data. Instead, create a function without this decorator."
                            },
                            "ruleId": "python.django.security.audit.csrf-exempt.no-csrf-exempt",
                        },
                        {
                            "fingerprints": {"matchBasedId/v1": "1cc62"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 9,
                                            "endLine": 17,
                                            "snippet": {
                                                "text": "@receiver(request_finished)\n@csrf_exempt\ndef foo():\n    pass"
                                            },
                                            "startColumn": 1,
                                            "startLine": 14,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Detected usage of @csrf_exempt, which indicates that there is no CSRF token set for this route. This could lead to an attacker manipulating the user's account and exfiltration of private data. Instead, create a function without this decorator."
                            },
                            "ruleId": "python.django.security.audit.csrf-exempt.no-csrf-exempt",
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
            num_changes=2,
        )
