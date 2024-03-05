import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.secure_flask_session_config import SecureFlaskSessionConfig


class TestSecureFlaskSessionConfig(BaseCodemodTest):
    codemod = SecureFlaskSessionConfig

    def test_name(self):
        assert self.codemod.name == "secure-flask-session-configuration"

    def test_no_flask_app(self, tmpdir):
        input_code = """
        import flask

        response = flask.Response()
        var = "hello"
        response.set_cookie("name", "value")
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_app_defined_separate_module(self, tmpdir):
        # TODO: test this as an integration test with two real modules
        input_code = """
        from my_app_module import app

        app.config["SESSION_COOKIE_SECURE"] = False
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_app_not_assigned(self, tmpdir):
        input_code = """
        import flask

        flask.Flask(__name__)
        print(1)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_app_accessed_config_not_called(self, tmpdir):
        input_code = """
        import flask

        app = flask.Flask(__name__)
        app.secret_key = "dev"
        # more code
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_app_update_no_keyword(self, tmpdir):
        input_code = """
        import flask

        from flask import Flask
        def foo(test_config=None):
            app = Flask(__name__)
            app.secret_key = "dev"
            app.config.update(test_config)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_from_import(self, tmpdir):
        input_code = """
        from flask import Flask

        app = Flask(__name__)
        app.secret_key = "dev"
        app.config.update(SESSION_COOKIE_SECURE=False)
        """
        expexted_output = """
        from flask import Flask

        app = Flask(__name__)
        app.secret_key = "dev"
        app.config.update(SESSION_COOKIE_SECURE=True)
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_import_alias(self, tmpdir):
        input_code = """
        from flask import Flask as flask_app
        app = flask_app(__name__)
        app.secret_key = "dev"
        # more code
        app.config.update(SESSION_COOKIE_SECURE=False)
        """
        expexted_output = """
        from flask import Flask as flask_app
        app = flask_app(__name__)
        app.secret_key = "dev"
        # more code
        app.config.update(SESSION_COOKIE_SECURE=True)
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_annotated_assign(self, tmpdir):
        input_code = """
        import flask
        app: flask.Flask = flask.Flask(__name__)
        app.secret_key = "dev"
        # more code
        app.config.update(SESSION_COOKIE_SECURE=False)
        """
        expexted_output = """
        import flask
        app: flask.Flask = flask.Flask(__name__)
        app.secret_key = "dev"
        # more code
        app.config.update(SESSION_COOKIE_SECURE=True)
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_other_assignment_type(self, tmpdir):
        input_code = """
        import flask
        class AppStore:
            pass
        store = AppStore()
        store.app = flask.Flask(__name__)
        store.app.secret_key = "dev"
        # more code
        store.app.config.update(SESSION_COOKIE_SECURE=False)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    @pytest.mark.parametrize(
        "config_lines,expected_config_lines,num_changes",
        [
            (
                """app.config""",
                """app.config""",
                0,
            ),
            (
                """app.config["TESTING"] = True""",
                """app.config["TESTING"] = True""",
                0,
            ),
            (
                """app.config.testing = True""",
                """app.config.testing = True""",
                0,
            ),
            (
                """app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')""",
                """app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')""",
                0,
            ),
            (
                """app.config.update(SESSION_COOKIE_SECURE=True)""",
                """app.config.update(SESSION_COOKIE_SECURE=True)""",
                0,
            ),
            (
                """app.config.update(SESSION_COOKIE_HTTPONLY=True)""",
                """app.config.update(SESSION_COOKIE_HTTPONLY=True)""",
                0,
            ),
            (
                """app.config.update(SESSION_COOKIE_HTTPONLY=False)""",
                """app.config.update(SESSION_COOKIE_HTTPONLY=True)""",
                1,
            ),
            (
                """app.config['SESSION_COOKIE_SECURE'] = False""",
                """app.config['SESSION_COOKIE_SECURE'] = True""",
                1,
            ),
            (
                """app.config['SESSION_COOKIE_HTTPONLY'] = False""",
                """app.config['SESSION_COOKIE_HTTPONLY'] = True""",
                1,
            ),
            (
                """app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
""",
                """app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
""",
                0,
            ),
            (
                """app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_SAMESITE"] = None
""",
                """app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
""",
                2,
            ),
            (
                """app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
""",
                """app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
""",
                2,
            ),
            (
                """app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_SECURE"] = True
""",
                """app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SECURE"] = True
""",
                1,
            ),
        ],
    )
    def test_config_accessed_variations(
        self, tmpdir, config_lines, expected_config_lines, num_changes
    ):
        input_code = f"""import flask
app = flask.Flask(__name__)
app.secret_key = "dev"
{config_lines}
"""
        expected_output = f"""import flask
app = flask.Flask(__name__)
app.secret_key = "dev"
{expected_config_lines}
"""
        self.run_and_assert(
            tmpdir, input_code, expected_output, num_changes=num_changes
        )

    @pytest.mark.skip()
    def test_func_scope(self, tmpdir):
        input_code = """
        from flask import Flask
        app = Flask(__name__)

        @app.route('/')
        def hello_world():
            return 'Hello World!'

        def configure():
            app.config['TESTING'] = True

        if __name__ == '__main__':
            configure()
            app.run()
        """
        expexted_output = """
        # TODO correct fix could be multiple options,
        # either within configure() call or after it's called
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)
