from core_codemods.sql_parameterization import SQLQueryParameterization
from tests.codemods.base_codemod_test import BaseCodemodTest
from textwrap import dedent


class TestSQLQueryParameterization(BaseCodemodTest):
    codemod = SQLQueryParameterization

    def test_name(self):
        assert self.codemod.name() == "sql-parameterization"

    def test_simple(self, tmpdir):
        input_code = """\
        import sqlite3
        from a import name

        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS where name ='" + name + "'")
        """
        expected = """\
        import sqlite3
        from a import name

        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS where name =?", (name, ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1
