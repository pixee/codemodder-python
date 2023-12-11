from core_codemods.flask_json_response_type import FlaskJsonResponseType
from tests.codemods.base_codemod_test import BaseCodemodTest
from textwrap import dedent


class TestFlaskJsonResponseType(BaseCodemodTest):
    codemod = FlaskJsonResponseType

    def test_name(self):
        assert self.codemod.name() == "flask-json-response-type"

    def test_simple(self, tmpdir):
        input_code = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return make_response(json_response)
        """
        expected = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (make_response(json_response), {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_simple_return_json(self, tmpdir):
        input_code = """\
        from flask import Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return json_response
        """
        expected = """\
        from flask import Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (json_response, {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_alias(self, tmpdir):
        input_code = """\
        from flask import make_response as response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return response(json_response)
        """
        expected = """\
        from flask import make_response as response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (response(json_response), {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_direct(self, tmpdir):
        input_code = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            return make_response(json.dumps({ "user_input": request.GET.get("input") }))
        """
        expected = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            return (make_response(json.dumps({ "user_input": request.GET.get("input") })), {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_tuple_no_dict(self, tmpdir):
        input_code = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            code = 404
            return (make_response(json_response), code)
        """
        expected = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            code = 404
            return (make_response(json_response), code, {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_tuple_dict_no_key(self, tmpdir):
        input_code = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (make_response(json_response), {})
        """
        expected = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (make_response(json_response), {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_triple_dict(self, tmpdir):
        input_code = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            code = 404
            return (make_response(json_response), code, {})
        """
        expected = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            code = 404
            return (make_response(json_response), code, {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_no_route_decorator(self, tmpdir):
        input_code = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return make_response(json_response)
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_content_type_set(self, tmpdir):
        input_code = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (make_response(json_response), {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_no_json_input(self, tmpdir):
        input_code = """\
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            dict_response = { "user_input": request.GET.get("input") }
            return make_response(dict_response)
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0
