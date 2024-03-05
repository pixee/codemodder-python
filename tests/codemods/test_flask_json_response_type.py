from codemodder.codemods.test import BaseCodemodTest
from core_codemods.flask_json_response_type import FlaskJsonResponseType


class TestFlaskJsonResponseType(BaseCodemodTest):
    codemod = FlaskJsonResponseType

    def test_name(self):
        assert self.codemod.name == "flask-json-response-type"

    def test_simple(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return make_response(json_response)
        """
        expected = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return make_response(json_response, {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_simple_indirect(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            response = make_response(json_response)
            return response
        """
        expected = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            response = make_response(json_response, {'Content-Type': 'application/json'})
            return response
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_simple_tuple_arg(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return make_response((json_response, 404))
        """
        expected = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return make_response((json_response, 404, {'Content-Type': 'application/json'}))
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_simple_return_json(self, tmpdir):
        input_code = """
        from flask import Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return json_response
        """
        expected = """
        from flask import Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (json_response, {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_simple_tuple(self, tmpdir):
        input_code = """
        from flask import Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (json_response, 404)
        """
        expected = """
        from flask import Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (json_response, 404, {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_alias(self, tmpdir):
        input_code = """
        from flask import make_response as response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return response(json_response)
        """
        expected = """
        from flask import make_response as response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return response(json_response, {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_indirect_dict(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            headers = {'key': 'value'}
            return make_response(json_response, headers)
        """
        expected = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            headers = {'key': 'value', 'Content-Type': 'application/json'}
            return make_response(json_response, headers)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_direct_return(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            return make_response(json.dumps({ "user_input": request.GET.get("input") }))
        """
        expected = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            return make_response(json.dumps({ "user_input": request.GET.get("input") }), {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_tuple_dict_no_key(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (make_response(json_response), {})
        """
        expected = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (make_response(json_response), {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_no_route_decorator(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return make_response(json_response)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_content_type_set(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (make_response(json_response), {'Content-Type': 'application/json'})
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_content_type_maybe_set_star(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json
        from foo import another_dict

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (make_response(json_response), {**another_dict})
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_content_type_maybe_set(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json
        from foo import key

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return (make_response(json_response), {key:'application/json'})
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_no_json_dumps_input(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            dict_response = { "user_input": request.GET.get("input") }
            return make_response(dict_response)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_unknown_call_response(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json
        from foo import bar

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            dict_response = { "user_input": request.GET.get("input") }
            return bar(dict_response)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_simple_indirect_content_type_set(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            response = make_response(json_response)
            response.headers['Content-Type'] = 'application/json'
            return response
        """
        self.run_and_assert(tmpdir, input_code, input_code)
