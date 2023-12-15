from core_codemods.add_requests_timeouts import AddRequestsTimeouts
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestAddRequestsTimeouts(BaseIntegrationTest):
    codemod = AddRequestsTimeouts
    code_path = "tests/samples/requests_timeout.py"

    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (2, 'requests.get("https://example.com", timeout=60)\n'),
            (5, 'requests.post("https://example.com", verify=False, timeout=60)\n'),
        ],
    )

    expected_diff = """\
--- 
+++ 
@@ -1,6 +1,6 @@
 import requests
 
-requests.get("https://example.com")
+requests.get("https://example.com", timeout=60)
 requests.get("https://example.com", timeout=1)
 requests.get("https://example.com", timeout=(1, 10), verify=False)
-requests.post("https://example.com", verify=False)
+requests.post("https://example.com", verify=False, timeout=60)
"""

    num_changes = 2
    expected_line_change = "3"
    change_description = AddRequestsTimeouts.CHANGE_DESCRIPTION
