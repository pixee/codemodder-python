import pytest
from core_codemods.secure_flask_session_config import SecureFlaskSessionConfig
from tests.codemods.base_codemod_test import BaseCodemodTest
from textwrap import dedent


class TestSecureFlaskSessionConfig(BaseCodemodTest):
    codemod = SecureFlaskSessionConfig

    def test_name(self):
        assert self.codemod.name() == "secure-flask-session-configuration"

    def test_no_flask_app(self, tmpdir):
        input_code = """\
        import flask

        response = flask.Response()
        var = "hello"
        response.set_cookie("name", "value")
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_app_not_accessed(self, tmpdir):
        input_code = """\
        import flask

        app = flask.Flask(__name__)
        # more code
        print(1)
        """
        expexted_output = """\
        import flask

        app = flask.Flask(__name__)
        # more code
        print(1)
        app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expexted_output))
        assert len(self.file_context.codemod_changes) == 1

    def test_app_defined_separate_module(self, tmpdir):
        # TODO: test this as an integration test with two real modules
        input_code = """\
        from my_app_module import app

        app.config["SESSION_COOKIE_SECURE"] = False
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_app_not_assigned(self, tmpdir):
        input_code = """\
        import flask

        flask.Flask(__name__)
        print(1)
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_app_accessed_config_not_called(self, tmpdir):
        input_code = """\
        import flask

        app = flask.Flask(__name__)
        app.secret_key = "dev"
        # more code
        """
        expexted_output = """\
        import flask

        app = flask.Flask(__name__)
        app.secret_key = "dev"
        app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')
        # more code
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expexted_output))
        assert len(self.file_context.codemod_changes) == 1

    def test_from_import(self, tmpdir):
        input_code = """\
        from flask import Flask

        app = flask.Flask(__name__)
        app.secret_key = "dev"
        # more code
        """
        expexted_output = """\
        from flask import Flask

        app = flask.Flask(__name__)
        app.secret_key = "dev"
        app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')
        # more code
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expexted_output))
        assert len(self.file_context.codemod_changes) == 1

    def test_import_alias(self, tmpdir):
        input_code = f"""\
        from flask import Flask as flask_app
        app = flask_app(__name__)
        app.secret_key = "dev"
        # more code
        """
        expexted_output = f"""\
        from flask import Flask as flask_app
        app = flask_app(__name__)
        app.secret_key = "dev"
        app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')
        # more code
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expexted_output))
        assert len(self.file_context.codemod_changes) == 1

    @pytest.mark.parametrize(
        "config_lines,expected_config_lines",
        [
            (
                """app.config""",
                """app.config
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')""",
            ),
            (
                """app.config["TESTING"] = True""",
                """app.config["TESTING"] = True
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')""",
            ),
            (
                """app.config.testing = True""",
                """app.config.testing = True
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')""",
            ),
            (
                """app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')""",
                """app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')""",
            ),
            (
                """app.config.update(SECRET_KEY='123SOMEKEY')
var = 1""",
                """app.config.update(SECRET_KEY='123SOMEKEY')
var = 1
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')""",
            ),
            (
                """app.config.update(SECRET_KEY='123SOMEKEY')""",
                """app.config.update(SECRET_KEY='123SOMEKEY')
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')""",
            ),
            (
                """app.config.update(SESSION_COOKIE_SECURE=True)""",
                """app.config.update(SESSION_COOKIE_SECURE=True)
app.config.update(SESSION_COOKIE_SAMESITE='Lax')""",
            ),
            (
                """app.config.update(SESSION_COOKIE_HTTPONLY=True)""",
                """app.config.update(SESSION_COOKIE_HTTPONLY=True)
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')""",
            ),
            (
                """app.config.update(SESSION_COOKIE_HTTPONLY=False)""",
                """app.config.update(SESSION_COOKIE_HTTPONLY=True)
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')""",
            ),
            (
                """app.config['SESSION_COOKIE_SECURE'] = False""",
                """app.config['SESSION_COOKIE_SECURE'] = True
app.config.update(SESSION_COOKIE_SAMESITE='Lax')""",
            ),
            (
                """app.config['SESSION_COOKIE_HTTPONLY'] = False""",
                """app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')""",
            ),
            (
                """app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
""",
                """app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
""",
            ),
            (
                """app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_SAMESITE"] = None
""",
                """app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
""",
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
            ),
            (
                """app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_SECURE"] = True
""",
                """app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SECURE"] = True
app.config.update(SESSION_COOKIE_SAMESITE='Lax')
""",
            ),
        ],
    )
    def test_config_accessed_variations(
        self, tmpdir, config_lines, expected_config_lines
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
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected_output))

    @pytest.mark.skip()
    def test_func_scope(self, tmpdir):
        input_code = """\
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
        expexted_output = """\
        # TODO correct fix could be multiple options,
        # either within configure() call or after it's called
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expexted_output))
        assert len(self.file_context.codemod_changes) == 1
