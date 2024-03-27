from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.flask_json_response_type import (
    FlaskJsonResponseType,
    FlaskJsonResponseTypeTransformer,
)


class TestFlaskJsonResponseType(BaseIntegrationTest):
    codemod = FlaskJsonResponseType
    original_code = """
    from flask import make_response, Flask
    import json
    
    app = Flask(__name__)
    
    @app.route("/test")
    def foo(request):
        json_response = json.dumps({ "user_input": request.GET.get("input") })
        return make_response(json_response)
    """
    replacement_lines = [
        (
            9,
            """    return make_response(json_response, {'Content-Type': 'application/json'})\n""",
        ),
    ]
    # fmt: off
    expected_diff = (
    """--- \n"""
    """+++ \n"""
    """@@ -6,4 +6,4 @@\n"""
    """ @app.route("/test")\n"""
    """ def foo(request):\n"""
    """     json_response = json.dumps({ "user_input": request.GET.get("input") })\n"""
    """-    return make_response(json_response)\n"""
    """+    return make_response(json_response, {'Content-Type': 'application/json'})\n"""
    )
    # fmt: on

    expected_line_change = "9"
    change_description = FlaskJsonResponseTypeTransformer.change_description
    num_changed_files = 1
