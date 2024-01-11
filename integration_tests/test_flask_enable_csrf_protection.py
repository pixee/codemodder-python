from core_codemods.flask_enable_csrf_protection import FlaskEnableCSRFProtection
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestFlaskEnableCSRFProtection(BaseIntegrationTest):
    codemod = FlaskEnableCSRFProtection
    code_path = "tests/samples/flask_enable_csrf_protection.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (1, """from flask_wtf.csrf import CSRFProtect\n"""),
            (2, """\n"""),
            (3, """app = Flask(__name__)\n"""),
            (4, """csrf_app = CSRFProtect(app)\n"""),
        ],
    )

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -1,3 +1,5 @@\n"""
    """ from flask import Flask\n"""
    """+from flask_wtf.csrf import CSRFProtect\n"""
    """ \n"""
    """ app = Flask(__name__)\n"""
    """+csrf_app = CSRFProtect(app)\n"""
    )
    # fmt: on

    expected_line_change = "3"
    change_description = FlaskEnableCSRFProtection.CHANGE_DESCRIPTION
    num_changed_files = 2
