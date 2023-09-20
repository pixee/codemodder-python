from core_codemods.upgrade_sslcontext_tls import UpgradeSSLContextTLS
from integration_tests.base_test import BaseIntegrationTest


class TestUpgradeWeakTLS(BaseIntegrationTest):
    codemod = UpgradeSSLContextTLS
    code_path = "tests/samples/weak_tls.py"
    original_code = "import ssl\n\nssl.SSLContext(ssl.PROTOCOL_SSLv2)\n"
    expected_new_code = "import ssl\n\nssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)\n"
    expected_diff = "--- \n+++ \n@@ -1,3 +1,3 @@\n import ssl\n \n-ssl.SSLContext(ssl.PROTOCOL_SSLv2)\n+ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)\n"
    expected_line_change = "3"
    change_description = UpgradeSSLContextTLS.CHANGE_DESCRIPTION
