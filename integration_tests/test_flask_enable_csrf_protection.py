from codemodder.codemods.test import BaseIntegrationTest
from codemodder.dependency import FlaskWTF
from core_codemods.flask_enable_csrf_protection import FlaskEnableCSRFProtection


class TestFlaskEnableCSRFProtection(BaseIntegrationTest):
    codemod = FlaskEnableCSRFProtection
    original_code = """
    from flask import Flask

    app = Flask(__name__)
    """
    replacement_lines = [
        (2, """from flask_wtf.csrf import CSRFProtect\n"""),
        (3, """\n"""),
        (4, """app = Flask(__name__)\n"""),
        (5, """csrf_app = CSRFProtect(app)\n"""),
    ]
    # fmt: off
    expected_diff = (
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
    change_description = FlaskEnableCSRFProtection.change_description
    num_changed_files = 2
    requirements_file_name = "requirements.txt"
    original_requirements = (
        "# file used to test dependency management\n"
        "requests==2.31.0\n"
        "black==23.7.*\n"
        "mypy~=1.4\n"
        "pylint>1\n"
    )
    expected_requirements = (
        "# file used to test dependency management\n"
        "requests==2.31.0\n"
        "black==23.7.*\n"
        "mypy~=1.4\n"
        "pylint>1\n"
        f"{FlaskWTF.requirement}\n"
    )
