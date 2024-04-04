from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.sonar.sonar_url_sandbox import SonarUrlSandbox
from core_codemods.url_sandbox import UrlSandboxTransformer


class TestSonarUrlSandbox(SonarIntegrationTest):
    codemod = SonarUrlSandbox
    code_path = "tests/samples/flask_request.py"
    replacement_lines = [
        (1, "from flask import Flask, request\n"),
        (2, "from security import safe_requests\n"),
        (10, "    safe_requests.get(url)\n"),
    ]
    expected_diff = '--- \n+++ \n@@ -1,5 +1,5 @@\n-import requests\n from flask import Flask, request\n+from security import safe_requests\n \n app = Flask(__name__)\n \n@@ -7,4 +7,4 @@\n @app.route("/example")\n def example():\n     url = request.args["url"]\n-    requests.get(url)\n+    safe_requests.get(url)\n'
    expected_line_change = "10"
    change_description = UrlSandboxTransformer.change_description
