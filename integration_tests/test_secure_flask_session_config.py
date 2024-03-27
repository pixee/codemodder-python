from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.secure_flask_session_config import SecureFlaskSessionConfig


class TestSecureFlaskSessionConfig(BaseIntegrationTest):
    codemod = SecureFlaskSessionConfig
    original_code = """
    from flask import Flask
    app = Flask(__name__)
    app.config['SESSION_COOKIE_HTTPONLY'] = False
    @app.route('/')
    def hello_world():
        return 'Hello World!'
    """
    replacement_lines = [(3, "app.config['SESSION_COOKIE_HTTPONLY'] = True\n")]
    expected_diff = "--- \n+++ \n@@ -1,6 +1,6 @@\n from flask import Flask\n app = Flask(__name__)\n-app.config['SESSION_COOKIE_HTTPONLY'] = False\n+app.config['SESSION_COOKIE_HTTPONLY'] = True\n @app.route('/')\n def hello_world():\n     return 'Hello World!'\n"
    expected_line_change = "3"
    change_description = SecureFlaskSessionConfig.change_description
