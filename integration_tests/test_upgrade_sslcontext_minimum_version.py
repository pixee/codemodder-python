from core_codemods.upgrade_sslcontext_minimum_version import (
    UpgradeSSLContextMinimumVersion,
)
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestUpgradeSSLContextMininumVersion(BaseIntegrationTest):
    codemod = UpgradeSSLContextMinimumVersion
    code_path = "tests/samples/upgrade_sslcontext_minimum_version.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (1, "import ssl\n\n"),
            (7, "my_ctx.minimum_version = ssl.TLSVersion.TLSv1_2\n"),
        ],
    )

    expected_diff = '--- \n+++ \n@@ -1,8 +1,9 @@\n from ssl import PROTOCOL_TLS_CLIENT, SSLContext, TLSVersion\n+import ssl\n \n my_ctx = SSLContext(protocol=PROTOCOL_TLS_CLIENT)\n \n print("FOO")\n \n my_ctx.maximum_version = TLSVersion.MAXIMUM_SUPPORTED\n-my_ctx.minimum_version = TLSVersion.TLSv1_1\n+my_ctx.minimum_version = ssl.TLSVersion.TLSv1_2\n'
    expected_line_change = "8"
    change_description = UpgradeSSLContextMinimumVersion.CHANGE_DESCRIPTION
