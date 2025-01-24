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
            5,
            """url = "https://example.com"\n""",
        ),
    ]
    # fmt: off
    expected_diff = (
    """--- \n"""
    """+++ \n"""
    """@@ -2,4 +2,4 @@\n"""
    ''' import smtplib\n'''
    ''' import telnetlib\n'''
    ''' \n'''
    '''-url = "http://example.com"\n'''
    '''+url = "https://example.com"\n'''
    )
    # fmt: on
    expected_line_change = "5"
    change_description = SonarUseSecureProtocolsTransformer.change_description
