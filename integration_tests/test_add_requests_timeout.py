from requests.exceptions import ConnectionError

from codemodder.codemods.test.integration_utils import BaseRemediationIntegrationTest
from core_codemods.add_requests_timeouts import (
    AddRequestsTimeouts,
    TransformAddRequestsTimeouts,
)


class TestAddRequestsTimeouts(BaseRemediationIntegrationTest):
    codemod = AddRequestsTimeouts
    original_code = """
    import requests
    
    requests.get("https://example.com")
    requests.get("https://example.com", timeout=1)
    requests.get("https://example.com", timeout=(1, 10), verify=False)
    requests.post("https://example.com", verify=False)
    """

    expected_diff_per_change = [
        '--- \n+++ \n@@ -1,6 +1,6 @@\n import requests\n \n-requests.get("https://example.com")\n+requests.get("https://example.com", timeout=60)\n requests.get("https://example.com", timeout=1)\n requests.get("https://example.com", timeout=(1, 10), verify=False)\n requests.post("https://example.com", verify=False)',
        '--- \n+++ \n@@ -3,4 +3,4 @@\n requests.get("https://example.com")\n requests.get("https://example.com", timeout=1)\n requests.get("https://example.com", timeout=(1, 10), verify=False)\n-requests.post("https://example.com", verify=False)\n+requests.post("https://example.com", verify=False, timeout=60)',
    ]

    num_changes = 2
    expected_lines_changed = [3, 6]
    change_description = TransformAddRequestsTimeouts.change_description
    # expected because requests are made
    allowed_exceptions = (ConnectionError,)
