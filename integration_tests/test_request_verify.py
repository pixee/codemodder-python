from requests import exceptions

from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.requests_verify import RequestsVerify


class TestRequestsVerify(BaseIntegrationTest):
    codemod = RequestsVerify
    original_code = """
    import requests

    requests.get("https://www.google.com", verify=False)
    requests.post("https://some-api/", json={"id": 1234, "price": 18}, verify=False)
    var = "hello"
    """

    replacement_lines = [
        (3, """requests.get("https://www.google.com", verify=True)\n"""),
        (
            4,
            """requests.post("https://some-api/", json={"id": 1234, "price": 18}, verify=True)\n""",
        ),
    ]
    expected_diff = '--- \n+++ \n@@ -1,5 +1,5 @@\n import requests\n \n-requests.get("https://www.google.com", verify=False)\n-requests.post("https://some-api/", json={"id": 1234, "price": 18}, verify=False)\n+requests.get("https://www.google.com", verify=True)\n+requests.post("https://some-api/", json={"id": 1234, "price": 18}, verify=True)\n var = "hello"\n'
    expected_line_change = "3"
    num_changes = 2
    change_description = RequestsVerify.change_description
    # expected because when executing the output code it will make a request which fails, which is OK.
    allowed_exceptions = (exceptions.ConnectionError,)
