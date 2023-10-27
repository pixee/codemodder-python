from core_codemods.secure_flask_cookie import SecureFlaskCookie
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestSecureFlaskCookie(BaseIntegrationTest):
    codemod = SecureFlaskCookie
    code_path = "tests/samples/flask_cookie.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (
                7,
                """    resp.set_cookie('custom_cookie', 'value', secure=True, httponly=True, samesite='Lax')\n""",
            ),
        ],
    )
    expected_diff = "--- \n+++ \n@@ -5,5 +5,5 @@\n @app.route('/')\n def index():\n     resp = make_response('Custom Cookie Set')\n-    resp.set_cookie('custom_cookie', 'value')\n+    resp.set_cookie('custom_cookie', 'value', secure=True, httponly=True, samesite='Lax')\n     return resp\n"
    expected_line_change = "8"
    change_description = SecureFlaskCookie.CHANGE_DESCRIPTION
