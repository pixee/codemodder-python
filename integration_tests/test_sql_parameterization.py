from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.sql_parameterization import (
    SQLQueryParameterization,
    SQLQueryParameterizationTransformer,
)


class TestSQLQueryParameterization(BaseIntegrationTest):
    codemod = SQLQueryParameterization
    original_code = """
    import sqlite3
    
    connection = sqlite3.connect(":memory:")
    connection.cursor().execute("CREATE TABLE Users (name, phone)")
    connection.cursor().execute("INSERT INTO Users VALUES ('Jenny','867-5309')")
    
    
    def foo(cursor: sqlite3.Cursor, name: str, phone: str):
        a = "SELECT * FROM Users"
        b = " WHERE name ='" + name
        c = "' AND phone = '" + phone + "'"
        r = cursor.execute(a + b + c)
        print(r.fetchone())
    
    
    foo(connection.cursor(), "Jenny", "867-5309")    
    """

    replacement_lines = [
        (10, """    b = " WHERE name =?"\n"""),
        (11, """    c = " AND phone = ?"\n"""),
        (12, """    r = cursor.execute(a + b + c, (name, phone, ))\n"""),
    ]

    # fmt: off
    expected_diff = (
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
    change_description = SQLQueryParameterizationTransformer.change_description
    num_changed_files = 1
