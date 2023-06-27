from collections import defaultdict
import libcst as cst
from libcst.codemod import CodemodContext
import pytest
from codemodder.codemods.url_sandbox import UrlSandbox


class TestUrlSandbox:
    RESULTS_BY_ID = defaultdict(
        list,
        {
            "sandbox-url-creation": [
                {
                    "fingerprints": {"matchBasedId/v1": "6fa4"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": "tests/samples/make_request.py",
                                    "uriBaseId": "%SRCROOT%",
                                },
                                "region": {
                                    "endColumn": 31,
                                    "endLine": 3,
                                    "snippet": {
                                        "text": "requests.get('www.google.com')"
                                    },
                                    "startColumn": 1,
                                    "startLine": 3,
                                },
                            }
                        },
                    ],
                    "message": {"text": "Unbounded URL creation"},
                    "properties": {},
                    "ruleId": "codemodder.codemods.semgrep.sandbox-url-creation",
                }
            ],
        },
    )

    def run_and_assert(self, input_code, expected):
        input_tree = cst.parse_module(input_code)
        command_instance = UrlSandbox(CodemodContext(), self.RESULTS_BY_ID)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expected

    def test_import_requests(self):
        input_code = """import requests

requests.get("www.google.com")
var = "hello"
"""
        expected = """from security import safe_requests

safe_requests.get("www.google.com")
var = "hello"
"""
        self.run_and_assert(input_code, expected)

    @pytest.mark.skip()
    def test_from_requests(self):
        input_code = """from requests import get

get("www.google.com")
var = "hello"
"""
        expected = """from security.safe_requests import get

get("www.google.com")
var = "hello"
"""
        self.run_and_assert(input_code, expected)

    def test_requests_nameerror(self):
        input_code = """requests.get("www.google.com")

import requests
"""
        expected = input_code
        self.run_and_assert(input_code, expected)

    @pytest.mark.parametrize(
        "input_code,expected",
        [
            (
                """import requests
import csv
requests.get("www.google.com")
csv.excel
""",
                """import csv
from security import safe_requests

safe_requests.get("www.google.com")
csv.excel
""",
            ),
            (
                """import requests
from csv import excel
requests.get("www.google.com")
excel
""",
                """from csv import excel
from security import safe_requests

safe_requests.get("www.google.com")
excel
""",
            ),
        ],
    )
    def test_requests_other_import_untouched(self, input_code, expected):
        self.run_and_assert(input_code, expected)

    def test_requests_multifunctions(self):
        # Test that `requests` import isn't removed if code uses part of the requests
        # library that isn't part of our codemods. If we add the function as one of
        # our codemods, this test would change.
        input_code = """import requests

requests.get("www.google.com")
requests.status_codes.codes.FORBIDDEN
        """

        expected = """import requests
from security import safe_requests

safe_requests.get("www.google.com")
requests.status_codes.codes.FORBIDDEN"""

        self.run_and_assert(input_code, expected)

    def test_custom_get(self):
        input_code = """from app_funcs import get

get("www.google.com")"""
        expected = input_code
        self.run_and_assert(input_code, expected)
