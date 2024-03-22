from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.secure_flask_cookie import SecureFlaskCookie


class TestSecureFlaskCookie(BaseIntegrationTest):
    codemod = SecureFlaskCookie
    original_code = """
    from flask import Flask, session, make_response

    app = Flask(__name__)
    
    @app.route('/')
    def index():
        resp = make_response('Custom Cookie Set')
        resp.set_cookie('custom_cookie', 'value')
        return resp
    """
    replacement_lines = [
        (
            8,
            """    resp.set_cookie('custom_cookie', 'value', secure=True, httponly=True, samesite='Lax')\n""",
        ),
    ]
    expected_diff = "--- \n+++ \n@@ -5,5 +5,5 @@\n @app.route('/')\n def index():\n     resp = make_response('Custom Cookie Set')\n-    resp.set_cookie('custom_cookie', 'value')\n+    resp.set_cookie('custom_cookie', 'value', secure=True, httponly=True, samesite='Lax')\n     return resp\n"
    expected_line_change = "8"
    change_description = SecureFlaskCookie.change_description
