from core_codemods.requests_verify import RequestsVerify
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from requests import exceptions


class TestRequestsVerify(BaseIntegrationTest):
    codemod = RequestsVerify
    code_path = "tests/samples/unverified_request.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (2, """requests.get("https://www.google.com", verify=True)\n"""),
            (
                3,
                """requests.post("https://some-api/", json={"id": 1234, "price": 18}, verify=True)\n""",
            ),
        ],
    )
    expected_diff = '--- \n+++ \n@@ -1,5 +1,5 @@\n import requests\n \n-requests.get("https://www.google.com", verify=False)\n-requests.post("https://some-api/", json={"id": 1234, "price": 18}, verify=False)\n+requests.get("https://www.google.com", verify=True)\n+requests.post("https://some-api/", json={"id": 1234, "price": 18}, verify=True)\n var = "hello"\n'
    expected_line_change = "3"
    num_changes = 2
    change_description = RequestsVerify.CHANGE_DESCRIPTION
    # expected because when executing the output code it will make a request which fails, which is OK.
    allowed_exceptions = (exceptions.ConnectionError,)
