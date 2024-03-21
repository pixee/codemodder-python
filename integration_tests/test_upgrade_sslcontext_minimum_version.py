from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.upgrade_sslcontext_minimum_version import (
    UpgradeSSLContextMinimumVersion,
)


class TestUpgradeSSLContextMininumVersion(BaseIntegrationTest):
    codemod = UpgradeSSLContextMinimumVersion
    original_code = """
    from ssl import PROTOCOL_TLS_CLIENT, SSLContext, TLSVersion

    my_ctx = SSLContext(protocol=PROTOCOL_TLS_CLIENT)
    
    print("FOO")
    
    my_ctx.maximum_version = TLSVersion.MAXIMUM_SUPPORTED
    my_ctx.minimum_version = TLSVersion.TLSv1_1
    """
    replacement_lines = [
        (2, "import ssl\n\n"),
        (8, "my_ctx.minimum_version = ssl.TLSVersion.TLSv1_2\n"),
    ]

    expected_diff = '--- \n+++ \n@@ -1,8 +1,9 @@\n from ssl import PROTOCOL_TLS_CLIENT, SSLContext, TLSVersion\n+import ssl\n \n my_ctx = SSLContext(protocol=PROTOCOL_TLS_CLIENT)\n \n print("FOO")\n \n my_ctx.maximum_version = TLSVersion.MAXIMUM_SUPPORTED\n-my_ctx.minimum_version = TLSVersion.TLSv1_1\n+my_ctx.minimum_version = ssl.TLSVersion.TLSv1_2\n'
    expected_line_change = "8"
    change_description = UpgradeSSLContextMinimumVersion.change_description
