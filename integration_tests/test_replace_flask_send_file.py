from core_codemods.replace_flask_send_file import (
    ReplaceFlaskSendFile,
)
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestReplaceFlaskSendFile(BaseIntegrationTest):
    codemod = ReplaceFlaskSendFile
    code_path = "tests/samples/replace_flask_send_file.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (0, """from flask import Flask\n"""),
            (1, """import flask\n"""),
            (2, """from pathlib import Path\n"""),
            (3, """\n"""),
            (4, """app = Flask(__name__)\n"""),
            (5, """\n"""),
            (6, """@app.route("/uploads/<path:name>")\n"""),
            (7, """def download_file(name):\n"""),
            (
                8,
                """    return flask.send_from_directory((p := Path(f'path/to/{name}.txt')).parent, p.name)\n""",
            ),
        ],
    )

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -1,7 +1,9 @@\n"""
    """-from flask import Flask, send_file\n"""
    """+from flask import Flask\n"""
    """+import flask\n"""
    """+from pathlib import Path\n"""
    """ \n"""
    """ app = Flask(__name__)\n"""
    """ \n"""
    """ @app.route("/uploads/<path:name>")\n"""
    """ def download_file(name):\n"""
    """-    return send_file(f'path/to/{name}.txt')\n"""
    """+    return flask.send_from_directory((p := Path(f'path/to/{name}.txt')).parent, p.name)\n"""

    )
    # fmt: on

    expected_line_change = "7"
    change_description = ReplaceFlaskSendFile.CHANGE_DESCRIPTION
    num_changed_files = 1
