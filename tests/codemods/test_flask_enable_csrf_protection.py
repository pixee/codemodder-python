from codemodder.codemods.test import BaseCodemodTest
from core_codemods.flask_enable_csrf_protection import FlaskEnableCSRFProtection


class TestFlaskEnableCSRFProtection(BaseCodemodTest):
    codemod = FlaskEnableCSRFProtection

    def test_name(self):
        assert self.codemod.name == "flask-enable-csrf-protection"

    def test_simple(self, tmpdir):
        input_code = """
        from flask import Flask
        app = Flask(__name__)
        """
        expected = """
        from flask import Flask
        from flask_wtf.csrf import CSRFProtect

        app = Flask(__name__)
        csrf_app = CSRFProtect(app)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_simple_alias(self, tmpdir):
        input_code = """
        from flask import Flask as Flosk
        app = Flosk(__name__)
        """
        expected = """
        from flask import Flask as Flosk
        from flask_wtf.csrf import CSRFProtect

        app = Flosk(__name__)
        csrf_app = CSRFProtect(app)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multiple(self, tmpdir):
        input_code = """
        from flask import Flask
        app = Flask(__name__)
        app2 = Flask(__name__)
        """
        expected = """
        from flask import Flask
        from flask_wtf.csrf import CSRFProtect

        app = Flask(__name__)
        csrf_app = CSRFProtect(app)
        app2 = Flask(__name__)
        csrf_app2 = CSRFProtect(app2)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=2)

    def test_multiple_inline(self, tmpdir):
        input_code = """
        from flask import Flask
        app = Flask(__name__); app2 = Flask(__name__)
        """
        expected = """
        from flask import Flask
        from flask_wtf.csrf import CSRFProtect

        app = Flask(__name__); app2 = Flask(__name__); csrf_app = CSRFProtect(app); csrf_app2 = CSRFProtect(app2)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multiple_inline_suite(self, tmpdir):
        input_code = """
        from flask import Flask
        if True: app = Flask(__name__); app2 = Flask(__name__)
        """
        expected = """
        from flask import Flask
        from flask_wtf.csrf import CSRFProtect

        if True: app = Flask(__name__); app2 = Flask(__name__); csrf_app = CSRFProtect(app); csrf_app2 = CSRFProtect(app2)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_simple_protected(self, tmpdir):
        input_code = """
        from flask import Flask
        from flask_wtf.csrf import CSRFProtect

        app = Flask(__name__)
        csrf_app = CSRFProtect(app)
        """
        self.run_and_assert(tmpdir, input_code, input_code)
