import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.defectdojo.semgrep.django_secure_set_cookie import (
    DjangoSecureSetCookie,
)


class TestDjangoSecureSetCookie(BaseSASTCodemodTest):
    codemod = DjangoSecureSetCookie
    tool = "defectdojo"

    def test_name(self):
        assert self.codemod._metadata.name == "django-secure-set-cookie"

    def test_simple(self, tmpdir):
        input_code = """
        response.set_cookie("name", "value")
        """
        expected = """
        response.set_cookie("name", "value", secure=True, httponly=True, samesite='Lax')
        """

        findings = {
            "results": [
                {
                    "title": "python.django.security.audit.secure-cookies.django-secure-set-cookie",
                    "file_path": "code.py",
                    "line": 2,
                },
            ]
        }

        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(findings))
