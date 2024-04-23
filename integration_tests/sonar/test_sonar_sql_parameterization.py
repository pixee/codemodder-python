from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.sonar.sonar_sql_parameterization import SonarSQLParameterization
from core_codemods.sql_parameterization import SQLQueryParameterizationTransformer


class TestSonarSQLParameterization(SonarIntegrationTest):
    codemod = SonarSQLParameterization
    code_path = "tests/samples/fix_sonar_sql_parameterization.py"
    replacement_lines = [
        (11, '    sql = """SELECT user FROM users WHERE user = ?"""\n'),
        (14, "    conn.cursor().execute(sql, ((user), ))\n"),
    ]
    expected_diff = """\
--- 
+++ 
@@ -8,7 +8,7 @@
 @app.route("/example")
 def f():
     user = request.args["user"]
-    sql = \"\"\"SELECT user FROM users WHERE user = \\'%s\\'\"\"\"
+    sql = \"\"\"SELECT user FROM users WHERE user = ?\"\"\"
 
     conn = sqlite3.connect("example")
-    conn.cursor().execute(sql % (user))
+    conn.cursor().execute(sql, ((user), ))
"""
    expected_line_change = "14"
    change_description = SQLQueryParameterizationTransformer.change_description
