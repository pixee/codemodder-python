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

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name ='" + name + "'")
        """
        expected = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name =?", (name, ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_multiple(self, tmpdir):
        input_code = """\
        import sqlite3

        name = input()
        phone = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name ='" + name + r"' AND phone ='" + phone + "'" )
        """
        expected = """\
        import sqlite3

        name = input()
        phone = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name =?" + r" AND phone =?",  (name, phone, ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_simple_with_quotes_in_middle(self, tmpdir):
        input_code = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name ='user_" + name + r"_system'")
        """
        expected = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name =?", ('user_{0}{1}'.format(name, r"_system"), ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_can_deal_with_multiple_variables(self, tmpdir):
        input_code = """\
        import sqlite3

        def foo(self, cursor, name, phone):

            a = "SELECT * from USERS "
            b = "WHERE name = '" + name
            c = "' AND phone = '" + phone + "'"
            return cursor.execute(a + b + c)
        """

        expected = """\
        import sqlite3

        def foo(self, cursor, name, phone):

            a = "SELECT * from USERS "
            b = "WHERE name = ?"
            c = " AND phone = ?"
            return cursor.execute(a + b + c, (name, phone, ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_simple_if(self, tmpdir):
        input_code = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name ='" + ('Jenny' if True else name) + "'")
        """
        expected = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name =?", (('Jenny' if True else name), ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_multiple_escaped_quote(self, tmpdir):
        input_code = """\
        import sqlite3

        name = input()
        phone = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute('SELECT * from USERS WHERE name =\\'' + name + '\\' AND phone =\\'' + phone + '\\'' )
        """
        expected = """\
        import sqlite3

        name = input()
        phone = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute('SELECT * from USERS WHERE name =?' + ' AND phone =?',  (name, phone, ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_simple_concatenated_strings(self, tmpdir):
        input_code = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS" "WHERE name ='" + name + "'")
        """
        expected = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS" "WHERE name =?", (name, ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1


class TestSQLQueryParameterizationFormattedString(BaseCodemodTest):
    codemod = SQLQueryParameterization

    def test_formatted_string_simple(self, tmpdir):
        input_code = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute(f"SELECT * from USERS WHERE name='{name}'")
        """
        expected = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute(f"SELECT * from USERS WHERE name=?", (name, ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_formatted_string_quote_in_middle(self, tmpdir):
        input_code = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute(f"SELECT * from USERS WHERE name='user_{name}_admin'")
        """
        expected = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute(f"SELECT * from USERS WHERE name=?", ('user_{0}_admin'.format(name), ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_formatted_string_with_literal(self, tmpdir):
        input_code = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute(f"SELECT * from USERS WHERE name='{name}_{1+2}'")
        """
        expected = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute(f"SELECT * from USERS WHERE name=?", ('{0}_{1}'.format(name, 1+2), ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_formatted_string_nested(self, tmpdir):
        input_code = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute(f"SELECT * from USERS WHERE name={f"'{name}'"}")
        """
        expected = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute(f"SELECT * from USERS WHERE name={f"?"}", (name, ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_formatted_string_concat_mixed(self, tmpdir):
        input_code = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name='" + f"{name}_{b'123'}" "'")
        """
        expected = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name=?", ('{0}_{1}'.format(name, b'123'), ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_multiple_expressions_injection(self, tmpdir):
        input_code = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name ='" + name + "_username" + "'")
        """
        expected = """\
        import sqlite3

        name = input()
        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name =?", ('{0}_username'.format(name), ))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1


class TestSQLQueryParameterizationNegative(BaseCodemodTest):
    codemod = SQLQueryParameterization

    # negative tests below
    def test_no_sql_keyword(self, tmpdir):
        input_code = """\
        import sqlite3

        def foo(self, cursor, name, phone):

            a = "COLLECT * from USERS "
            b = "WHERE name = '" + name
            c = "' AND phone = '" + phone + "'"
            return cursor.execute(a + b + c)
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_wont_mess_with_byte_strings(self, tmpdir):
        input_code = """\
        import sqlite3

        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE " + b"name ='" + str(1234) + b"'")
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_wont_parameterize_literals(self, tmpdir):
        input_code = """\
        import sqlite3

        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name ='" + str(1234) + "'")
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_wont_parameterize_literals_if(self, tmpdir):
        input_code = """\
        import sqlite3

        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name ='" + ('Jenny' if True else 'Lorelei') + "'")
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_will_ignore_escaped_quote(self, tmpdir):
        input_code = """\
        import sqlite3

        connection = sqlite3.connect("my_db.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * from USERS WHERE name ='Jenny\'s username'")
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_already_has_parameters(self, tmpdir):
        input_code = """\
        import sqlite3

        def foo(self, cursor, name, phone):

            a = "SELECT * from USERS "
            b = "WHERE name = '" + name
            c = "' AND phone = ?"
            return cursor.execute(a + b + c, (phone,))
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_wont_change_class_attribute(self, tmpdir):
        # query may be accesed from outside the module by importing A
        input_code = """\
        import sqlite3


        class A():

            query = "SELECT * from USERS WHERE name ='"

            def foo(self, name, cursor):
                return cursor.execute(query + name + "'")
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_wont_change_module_variable(self, tmpdir):
        # query may be accesed from outside the module by importing it
        input_code = """\
        import sqlite3

        query = "SELECT * from USERS WHERE name ='"

        def foo(name, cursor):
            return cursor.execute(query + name + "'")
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0
