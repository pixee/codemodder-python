from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.https_connection import HTTPSConnection


class TestHTTPSConnection(BaseIntegrationTest):
    codemod = HTTPSConnection
    original_code = """
    import urllib3
    import urllib3.connectionpool as pool
    from urllib3 import HTTPConnectionPool as something
    
    urllib3.HTTPConnectionPool("localhost", "80")
    urllib3.connectionpool.HTTPConnectionPool("localhost", "80")
    something("localhost", "80")
    pool.HTTPConnectionPool("localhost", "80")
    """

    replacement_lines = [
        (3, ""),
        (5, 'urllib3.HTTPSConnectionPool("localhost", "80")\n'),
        (6, 'urllib3.connectionpool.HTTPSConnectionPool("localhost", "80")\n'),
        (7, 'urllib3.HTTPSConnectionPool("localhost", "80")\n'),
        (8, 'pool.HTTPSConnectionPool("localhost", "80")\n'),
    ]
    expected_diff = '--- \n+++ \n@@ -1,8 +1,7 @@\n import urllib3\n import urllib3.connectionpool as pool\n-from urllib3 import HTTPConnectionPool as something\n \n-urllib3.HTTPConnectionPool("localhost", "80")\n-urllib3.connectionpool.HTTPConnectionPool("localhost", "80")\n-something("localhost", "80")\n-pool.HTTPConnectionPool("localhost", "80")\n+urllib3.HTTPSConnectionPool("localhost", "80")\n+urllib3.connectionpool.HTTPSConnectionPool("localhost", "80")\n+urllib3.HTTPSConnectionPool("localhost", "80")\n+pool.HTTPSConnectionPool("localhost", "80")\n'
    expected_line_change = "5"
    num_changes = 4
    change_description = HTTPSConnection.change_description
