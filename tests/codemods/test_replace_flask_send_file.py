from codemodder.codemods.test import BaseCodemodTest
from core_codemods.replace_flask_send_file import ReplaceFlaskSendFile


class TestReplaceFlaskSendFile(BaseCodemodTest):
    codemod = ReplaceFlaskSendFile

    def test_name(self):
        assert self.codemod.name == "replace-flask-send-file"

    def test_direct_string(self, tmpdir):
        input_code = """
        from flask import Flask, send_file

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            return send_file(f'path/to/{name}.txt')
        """
        expected = """
        from flask import Flask
        import flask
        from pathlib import Path

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            return flask.send_from_directory((p := Path(f'path/to/{name}.txt')).parent, p.name)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_direct_simple_string(self, tmpdir):
        input_code = """
        from flask import Flask, send_file

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            return send_file('path/to/file.txt')
        """
        expected = """
        from flask import Flask
        import flask
        from pathlib import Path

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            return flask.send_from_directory((p := Path('path/to/file.txt')).parent, p.name)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_direct_string_convert_arguments(self, tmpdir):
        input_code = """
        from flask import Flask, send_file

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            return send_file(f'path/to/{name}.txt', None, False, download_name = True)
        """
        expected = """
        from flask import Flask
        import flask
        from pathlib import Path

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            return flask.send_from_directory((p := Path(f'path/to/{name}.txt')).parent, p.name, mimetype = None, as_attachment = False, download_name = True)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_direct_path(self, tmpdir):
        input_code = """
        from flask import Flask, send_file
        from pathlib import Path

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            return send_file(Path(f'path/to/{name}.txt'))
        """
        expected = """
        from flask import Flask
        from pathlib import Path
        import flask

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            return flask.send_from_directory((p := Path(f'path/to/{name}.txt')).parent, p.name)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_indirect_path(self, tmpdir):
        input_code = """
        from flask import Flask, send_file
        from pathlib import Path

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            path = Path(f'path/to/{name}.txt')
            return send_file(path)
        """
        expected = """
        from flask import Flask
        from pathlib import Path
        import flask

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            path = Path(f'path/to/{name}.txt')
            return flask.send_from_directory(path.parent, path.name)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_indirect_path_alias(self, tmpdir):
        input_code = """
        from flask import Flask, send_file as send
        from pathlib import Path

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            path = Path(f'path/to/{name}.txt')
            return send(path)
        """
        expected = """
        from flask import Flask
        from pathlib import Path
        import flask

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            path = Path(f'path/to/{name}.txt')
            return flask.send_from_directory(path.parent, path.name)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_indirect_string(self, tmpdir):
        input_code = """
        from flask import Flask, send_file

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            path = f'path/to/{name}.txt'
            return send_file(path)
        """
        expected = """
        from flask import Flask
        import flask
        from pathlib import Path

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            path = f'path/to/{name}.txt'
            return flask.send_from_directory((p := Path(path)).parent, p.name)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_unknown_type(self, tmpdir):
        input_code = """
        from flask import Flask, send_file

        app = Flask(__name__)

        @app.route("/uploads/<path:name>")
        def download_file(name):
            return send_file(name)
        """
        self.run_and_assert(tmpdir, input_code, input_code)
