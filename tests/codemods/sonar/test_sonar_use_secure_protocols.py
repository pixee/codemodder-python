import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_use_secure_protocols import SonarUseSecureProtocols


class TestSonarUseSecureProtocols(BaseSASTCodemodTest):
    codemod = SonarUseSecureProtocols
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "use-secure-protocols"

    def test_replace_in_strings(self, tmpdir):
        input_code = """\
        url = "http://example.com"
        """
        expected = """\
        url = "https://example.com"
        """
        issues = {
            "hotspots": [
                {
                    "component": "code.py",
                    "status": "TO_REVIEW",
                    "textRange": {
                        "startLine": 1,
                        "endLine": 1,
                        "startOffset": 6,
                        "endOffset": 26,
                    },
                    "ruleKey": "python:S5332",
                },
            ],
        }
        self.run_and_assert(
            tmpdir, input_code, expected, results=json.dumps(issues), num_changes=1
        )

    def test_ftp_call(self, tmpdir):
        input_code = """\
        import ftplib
        ftp_con = ftplib.FTP("ftp.example.com")
        """
        expected = """\
        import ftplib
        ftp_con = ftplib.FTP_TLS("ftp.example.com")
        """
        issues = {
            "hotspots": [
                {
                    "component": "code.py",
                    "status": "TO_REVIEW",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 10,
                        "endOffset": 39,
                    },
                    "ruleKey": "python:S5332",
                },
            ],
        }
        self.run_and_assert(
            tmpdir, input_code, expected, results=json.dumps(issues), num_changes=1
        )

    def test_smtp_call(self, tmpdir):
        input_code = """\
        import smtplib
        smtp_con = smtplib.SMTP("smtp.example.com", port=587)
        """
        expected = """\
        import smtplib
        import ssl

        smtp_context = ssl.create_default_context()
        smtp_context.verify_mode = ssl.CERT_REQUIRED
        smtp_context.check_hostname = True
        smtp_con = smtplib.SMTP("smtp.example.com", port=587)
        smtplib.starttls(context=smtp_context)
        """
        issues = {
            "hotspots": [
                {
                    "component": "code.py",
                    "status": "TO_REVIEW",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 11,
                        "endOffset": 53,
                    },
                    "ruleKey": "python:S5332",
                },
            ],
        }
        self.run_and_assert(
            tmpdir, input_code, expected, results=json.dumps(issues), num_changes=1
        )

    def test_smtp_call_default_port(self, tmpdir):
        input_code = """\
        import smtplib
        smtp_con = smtplib.SMTP("smtp.example.com", port=0)
        """
        expected = """\
        import smtplib
        import ssl

        smtp_context = ssl.create_default_context()
        smtp_context.verify_mode = ssl.CERT_REQUIRED
        smtp_context.check_hostname = True
        smtp_con = smtplib.SMTP_SSL("smtp.example.com", port=0, context = smtp_context)
        """
        issues = {
            "hotspots": [
                {
                    "component": "code.py",
                    "status": "TO_REVIEW",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 11,
                        "endOffset": 51,
                    },
                    "ruleKey": "python:S5332",
                },
            ],
        }
        self.run_and_assert(
            tmpdir, input_code, expected, results=json.dumps(issues), num_changes=1
        )
