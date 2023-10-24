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
            (9, """    b = " WHERE name =?"\n"""),
            (10, """    c = " AND phone = ?"\n"""),
            (11, """    r = cursor.execute(a + b + c, (name, phone, ))\n"""),
        ],
    )

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -7,9 +7,9 @@\n"""
    """ \n"""
    """ def foo(cursor: sqlite3.Cursor, name: str, phone: str):\n"""
    """     a = "SELECT * FROM Users"\n"""
    """-    b = " WHERE name ='" + name\n"""
    """-    c = "' AND phone = '" + phone + "'"\n"""
    """-    r = cursor.execute(a + b + c)\n"""
    """+    b = " WHERE name =?"\n"""
    """+    c = " AND phone = ?"\n"""
    """+    r = cursor.execute(a + b + c, (name, phone, ))\n"""
    """     print(r.fetchone())\n"""
    """ \n"""
    """ \n""")
    # fmt: on

    expected_line_change = "12"
    change_description = SQLQueryParameterization.CHANGE_DESCRIPTION
    num_changed_files = 1
