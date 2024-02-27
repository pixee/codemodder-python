from core_codemods.flask_enable_csrf_protection import FlaskEnableCSRFProtection
from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from codemodder.dependency import FlaskWTF


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
    change_description = FlaskEnableCSRFProtection.change_description
    num_changed_files = 2

    requirements_path = "tests/samples/requirements.txt"
    original_requirements = "# file used to test dependency management\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n"
    expected_new_reqs = (
        f"# file used to test dependency management\n"
        "requests==2.31.0\n"
        "black==23.7.*\n"
        "mypy~=1.4\n"
        "pylint>1\n"
        f"{FlaskWTF.requirement} \\\n"
        f"{FlaskWTF.build_hashes()}"
    )
