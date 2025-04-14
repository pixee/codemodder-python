from codemodder.codemods.test.integration_utils import SonarRemediationIntegrationTest
from core_codemods.sonar.sonar_secure_cookie import (
    SonarSecureCookie,
    SonarSecureCookieTransformer,
)


class TestSonarSecureCookie(SonarRemediationIntegrationTest):
    codemod = SonarSecureCookie
    code_path = "tests/samples/secure_cookie.py"
    expected_diff_per_change = [
        "--- \n+++ \n@@ -5,5 +5,5 @@\n @app.route('/')\n def index():\n     resp = make_response('Custom Cookie Set')\n-    resp.set_cookie('custom_cookie', 'value')\n+    resp.set_cookie('custom_cookie', 'value', secure=True, httponly=True, samesite='Lax')\n     return resp\n",
        "--- \n+++ \n@@ -5,5 +5,5 @@\n @app.route('/')\n def index():\n     resp = make_response('Custom Cookie Set')\n-    resp.set_cookie('custom_cookie', 'value')\n+    resp.set_cookie('custom_cookie', 'value', secure=True, httponly=True, samesite='Lax')\n     return resp\n",
    ]

    expected_lines_changed = [8, 8]
    num_changes = 2
    change_description = SonarSecureCookieTransformer.change_description
