from core_codemods.https_connection import HTTPSConnection
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestHTTPSConnection(BaseIntegrationTest):
    codemod = HTTPSConnection
    code_path = "tests/samples/http_connection.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (2, ""),
            (4, 'urllib3.HTTPSConnectionPool("localhost", "80")\n'),
            (5, 'urllib3.connectionpool.HTTPSConnectionPool("localhost", "80")\n'),
            (6, 'urllib3.HTTPSConnectionPool("localhost", "80")\n'),
            (7, 'pool.HTTPSConnectionPool("localhost", "80")\n'),
        ],
    )

    expected_diff = '--- \n+++ \n@@ -1,8 +1,7 @@\n import urllib3\n import urllib3.connectionpool as pool\n-from urllib3 import HTTPConnectionPool as something\n \n-urllib3.HTTPConnectionPool("localhost", "80")\n-urllib3.connectionpool.HTTPConnectionPool("localhost", "80")\n-something("localhost", "80")\n-pool.HTTPConnectionPool("localhost", "80")\n+urllib3.HTTPSConnectionPool("localhost", "80")\n+urllib3.connectionpool.HTTPSConnectionPool("localhost", "80")\n+urllib3.HTTPSConnectionPool("localhost", "80")\n+pool.HTTPSConnectionPool("localhost", "80")\n'
    expected_line_change = "5"
    num_changes = 4
    change_description = HTTPSConnection.CHANGE_DESCRIPTION
