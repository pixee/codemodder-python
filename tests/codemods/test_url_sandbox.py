import pytest
from core_codemods.url_sandbox import UrlSandbox
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest


class TestUrlSandbox(BaseSemgrepCodemodTest):
    codemod = UrlSandbox

    def test_rule_ids(self):
        assert self.codemod.METADATA.NAME == "url-sandbox"

    def test_import_requests(self, tmpdir):
        input_code = """import requests

requests.get("www.google.com")
var = "hello"
"""
        expected = """from security import safe_requests

safe_requests.get("www.google.com")
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_from_requests(self, tmpdir):
        input_code = """from requests import get

get("www.google.com")
var = "hello"
"""
        expected = """from security.safe_requests import get

get("www.google.com")
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_requests_nameerror(self, tmpdir):
        input_code = """requests.get("www.google.com")

import requests
"""
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

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
    def test_requests_other_import_untouched(self, tmpdir, input_code, expected):
        self.run_and_assert(tmpdir, input_code, expected)

    def test_requests_multifunctions(self, tmpdir):
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

        self.run_and_assert(tmpdir, input_code, expected)

    def test_custom_get(self, tmpdir):
        input_code = """from app_funcs import get

get("www.google.com")"""
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    def test_ambiguous_get(self, tmpdir):
        input_code = """from requests import get

def get(url):
    pass

get("www.google.com")"""
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    def test_from_requests_with_alias(self, tmpdir):
        input_code = """from requests import get as got

got("www.google.com")
var = "hello"
"""
        expected = """from security.safe_requests import get as got

got("www.google.com")
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_requests_with_alias(self, tmpdir):
        input_code = """import requests as req

req.get("www.google.com")
var = "hello"
"""
        expected = """from security import safe_requests

safe_requests.get("www.google.com")
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)
