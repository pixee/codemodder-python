from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.sonar.sonar_use_secure_protocols import (
    SonarUseSecureProtocols,
    SonarUseSecureProtocolsTransformer,
)


class TestSonarUseSecureProtocols(SonarIntegrationTest):
    codemod = SonarUseSecureProtocols
    code_path = "tests/samples/use_secure_protocols.py"
    replacement_lines = [
        (
            4,
            """url = "https://example.com"\n""",
        ),
    ]
    # fmt: off
    expected_diff = (
    """--- \n"""
    """+++ \n"""
    """@@ -1,4 +1,4 @@\n"""
    ''' import ftplib\n'''
    ''' import smtplib\n'''
    ''' \n'''
    '''-url = "http://example.com"\n'''
    '''+url = "https://example.com"\n'''
    )
    # fmt: on
    expected_line_change = "4"
    change_description = SonarUseSecureProtocolsTransformer.change_description
