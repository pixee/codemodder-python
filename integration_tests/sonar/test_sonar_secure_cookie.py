from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.sonar.sonar_secure_cookie import (
    SonarSecureCookie,
    SonarSecureCookieTransformer,
)


class TestSonarSecureCookie(SonarIntegrationTest):
    codemod = SonarSecureCookie
    code_path = "tests/samples/secure_cookie.py"
    replacement_lines = [
        (
            8,
            """    resp.set_cookie('custom_cookie', 'value', secure=True, httponly=True, samesite='Lax')\n""",
        ),
    ]
    expected_diff = "--- \n+++ \n@@ -5,5 +5,5 @@\n @app.route('/')\n def index():\n     resp = make_response('Custom Cookie Set')\n-    resp.set_cookie('custom_cookie', 'value')\n+    resp.set_cookie('custom_cookie', 'value', secure=True, httponly=True, samesite='Lax')\n     return resp\n"
    expected_line_change = "8"
    change_description = SonarSecureCookieTransformer.change_description
