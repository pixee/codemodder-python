from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.replace_flask_send_file import ReplaceFlaskSendFile


class TestReplaceFlaskSendFile(BaseIntegrationTest):
    codemod = ReplaceFlaskSendFile
    original_code = """
    from flask import Flask, send_file

    app = Flask(__name__)
    
    @app.route("/uploads/<path:name>")
    def download_file(name):
        return send_file(f'path/to/{name}.txt')
    """
    replacement_lines = [
        (1, """from flask import Flask\n"""),
        (2, """import flask\n"""),
        (3, """from pathlib import Path\n"""),
        (4, """\n"""),
        (5, """app = Flask(__name__)\n"""),
        (6, """\n"""),
        (7, """@app.route("/uploads/<path:name>")\n"""),
        (8, """def download_file(name):\n"""),
        (
            9,
            """    return flask.send_from_directory((p := Path(f'path/to/{name}.txt')).parent, p.name)\n""",
        ),
    ]
    # fmt: off
    expected_diff = (
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
    change_description = ReplaceFlaskSendFile.change_description
    num_changed_files = 1
