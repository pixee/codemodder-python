from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.upgrade_sslcontext_tls import UpgradeSSLContextTLS


class TestUpgradeWeakTLS(BaseIntegrationTest):
    codemod = UpgradeSSLContextTLS

    original_code = """
    import ssl

    ssl.SSLContext(ssl.PROTOCOL_SSLv2)
    """
    expected_new_code = """
    import ssl

    ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    """
    expected_diff = "--- \n+++ \n@@ -1,3 +1,3 @@\n import ssl\n \n-ssl.SSLContext(ssl.PROTOCOL_SSLv2)\n+ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)"
    expected_line_change = "3"
    change_description = UpgradeSSLContextTLS.change_description
