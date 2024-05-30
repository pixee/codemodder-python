import json
from pathlib import Path

import pytest

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_sql_parameterization import SonarSQLParameterization

SAMPLE_FILE_PATH = (
    Path(__file__).parents[2] / "samples" / "sonar" / "sql_parameterization.json"
)


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

    @pytest.mark.xfail(reason="TODO: See issue #607")
    def test_more_complicated_example(self, tmpdir):
        input_code = """
        from django.shortcuts import redirect
        from django.http import HttpResponse

        import sqlite3
        import json


        def do_useful_things(request):
            if request.method == "POST":
                user = request.POST.get("user")

                sql = "SELECT user FROM users WHERE user = '%s'"
                conn = sqlite3.connect("example")
                result = conn.cursor().execute(sql % user)

                json_response = json.dumps({"user": result.fetchone()[0]})
                return HttpResponse(json_response.encode("utf-8"))
            else:
                return redirect("/")
        """.lstrip(
            "\n"
        )
        expected = """
        from django.shortcuts import redirect
        from django.http import HttpResponse

        import sqlite3
        import json


        def do_useful_things(request):
            if request.method == "POST":
                user = request.POST.get("user")

                sql = "SELECT user FROM users WHERE user = ?"
                conn = sqlite3.connect("example")
                result = conn.cursor().execute(sql, (user, ))

                json_response = json.dumps({"user": result.fetchone()[0]})
                return HttpResponse(json_response.encode("utf-8"))
            else:
                return redirect("/")
        """.lstrip(
            "\n"
        )

        issues = json.loads(SAMPLE_FILE_PATH.read_text())

        filename = Path(tmpdir) / "introduction" / "new_view.py"
        filename.parent.mkdir(parents=True)

        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            files=[filename],
            results=json.dumps(issues),
        )
