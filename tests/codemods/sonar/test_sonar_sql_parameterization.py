import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_sql_parameterization import SonarSQLParameterization


class TestSonarSQLParameterization(BaseSASTCodemodTest):
    codemod = SonarSQLParameterization
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "sql-parameterization-S3649"

    def test_simple(self, tmpdir):
        input_code = """
        import sqlite3

        from flask import Flask, request

        app = Flask(__name__)

        @app.route("/example")
        def f():
            user = request.args["user"]
            sql = '''SELECT user FROM users WHERE user = \'%s\' '''

            conn = sqlite3.connect("example")
            conn.cursor().execute(sql % (user))
        """
        expected = """
        import sqlite3

        from flask import Flask, request

        app = Flask(__name__)

        @app.route("/example")
        def f():
            user = request.args["user"]
            sql = '''SELECT user FROM users WHERE user = ? '''

            conn = sqlite3.connect("example")
            conn.cursor().execute(sql, ((user), ))
        """
        issues = {
            "issues": [
                {
                    "rule": "pythonsecurity:S3649",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 14,
                        "endLine": 14,
                        "startOffset": 4,
                        "endOffset": 39,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
