from core_codemods.sql_parameterization import SQLQueryParameterization
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestSQLQueryParameterization(BaseIntegrationTest):
    codemod = SQLQueryParameterization
    code_path = "tests/samples/sql_injection.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (6, """    b = " WHERE name =?"\n"""),
            (7, """    c = " AND phone = ?"\n""" ),
            (8, """    r = cursor.execute(a + b + c, (name, phone, ))\n"""),
        ],
    )

    expected_diff ="""\
--- 
+++ 
@@ -4,9 +4,9 @@
 
 def foo(cursor: sqlite3.Cursor, name: str, phone:str):
     a = "SELECT * FROM Users"
-    b = " WHERE name ='" + name
-    c = "' AND phone = '" + phone + "'"
-    r = cursor.execute(a + b + c)
+    b = " WHERE name =?"
+    c = " AND phone = ?"
+    r = cursor.execute(a + b + c, (name, phone, ))
     print(r.fetchone())
 
 foo(connection.cursor(), 'Jenny', '867-5309')
"""
    expected_line_change = "9"
    change_description = SQLQueryParameterization.CHANGE_DESCRIPTION
    num_changed_files = 1
