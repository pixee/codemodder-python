from requests import exceptions

from codemodder.codemods.test.integration_utils import BaseRemediationIntegrationTest
from core_codemods.requests_verify import RequestsVerify


class TestRequestsVerify(BaseRemediationIntegrationTest):
    codemod = RequestsVerify
    original_code = """
    import requests

    requests.get("https://www.google.com", verify=False)
    requests.post("https://some-api/", json={"id": 1234, "price": 18}, verify=False)
    var = "hello"
    """

    expected_diff_per_change = [
        '--- \n+++ \n@@ -1,5 +1,5 @@\n import requests\n \n-requests.get("https://www.google.com", verify=False)\n+requests.get("https://www.google.com", verify=True)\n requests.post("https://some-api/", json={"id": 1234, "price": 18}, verify=False)\n var = "hello"',
        '--- \n+++ \n@@ -1,5 +1,5 @@\n import requests\n \n requests.get("https://www.google.com", verify=False)\n-requests.post("https://some-api/", json={"id": 1234, "price": 18}, verify=False)\n+requests.post("https://some-api/", json={"id": 1234, "price": 18}, verify=True)\n var = "hello"',
    ]

    expected_lines_changed = [3, 4]
    num_changes = 2
    change_description = RequestsVerify.change_description
    # expected because when executing the output code it will make a request which fails, which is OK.
    allowed_exceptions = (exceptions.ConnectionError,)
