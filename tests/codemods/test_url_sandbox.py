import libcst as cst
from libcst.codemod import CodemodContext
import pytest
from codemodder.codemods.url_sandbox import UrlSandbox


class TestUrlSandbox:
    def run_and_assert(self, input_code, expexted_output):
        input_tree = cst.parse_module(input_code)
        command_instance = UrlSandbox(CodemodContext())
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expexted_output

    @pytest.mark.parametrize(
        "input_code,expexted_output",
        [
            (
                """import requests

requests.get("www.google.com")
var = "hello"
        """,
                """import safe_requests

safe_requests.get("www.google.com")
var = "hello"
        """,
            ),
            (
                """from requests import get

get("www.google.com")
var = "hello"
            """,
                """from safe_requests import get

get("www.google.com")
var = "hello"
            """,
            ),
        ],
    )
    def test_requests(self, input_code, expexted_output):
        self.run_and_assert(input_code, expexted_output)

    @pytest.mark.skip()
    def test_requests_nameerror(self):
        input_code = """requests.get("www.google.com")

import requests
            """
        expexted_output = input_code
        self.run_and_assert(input_code, expexted_output)

    @pytest.mark.skip()
    def test_requests_multifunctions(self):
        # Test that `requests` import isn't removed if code uses part of the requests
        # library that isn't part of our codemods. If we add the function as one of
        # our codemods, this test would change.
        input_code = """import requests

requests.get("www.google.com")
requests.status_codes.codes.FORBIDDEN
        """

        expexted_output = """import requests
import safe_requests

safe_requests.get("www.google.com")
requests.status_codes.codes.FORBIDDEN
    """

        self.run_and_assert(input_code, expexted_output)

    @pytest.mark.skip()
    def test_custom_get(self):
        input_code = """from app_funcs import get

get("www.google.com")
    """
        expexted_output = input_code
        self.run_and_assert(input_code, expexted_output)
