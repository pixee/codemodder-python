from requests.exceptions import ConnectionError

from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.add_requests_timeouts import (
    AddRequestsTimeouts,
    TransformAddRequestsTimeouts,
)


class TestAddRequestsTimeouts(BaseIntegrationTest):
    codemod = AddRequestsTimeouts
    original_code = """
    import requests
    
    requests.get("https://example.com")
    requests.get("https://example.com", timeout=1)
    requests.get("https://example.com", timeout=(1, 10), verify=False)
    requests.post("https://example.com", verify=False)
    """

    replacement_lines = [
        (3, 'requests.get("https://example.com", timeout=60)\n'),
        (6, 'requests.post("https://example.com", verify=False, timeout=60)\n'),
    ]

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
    change_description = TransformAddRequestsTimeouts.change_description
    # expected because requests are made
    allowed_exceptions = (ConnectionError,)
