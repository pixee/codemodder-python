from core_codemods.secure_flask_session_config import SecureFlaskSessionConfig
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestSecureFlaskSessionConfig(BaseIntegrationTest):
    codemod = SecureFlaskSessionConfig
    code_path = "tests/samples/flask_app.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path, [(2, "app.config['SESSION_COOKIE_HTTPONLY'] = True\n")]
    )
    expected_diff = "--- \n+++ \n@@ -1,6 +1,6 @@\n from flask import Flask\n app = Flask(__name__)\n-app.config['SESSION_COOKIE_HTTPONLY'] = False\n+app.config['SESSION_COOKIE_HTTPONLY'] = True\n @app.route('/')\n def hello_world():\n     return 'Hello World!'\n"
    expected_line_change = "3"
    change_description = SecureFlaskSessionConfig.CHANGE_DESCRIPTION
