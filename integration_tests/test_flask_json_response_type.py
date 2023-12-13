from core_codemods.flask_json_response_type import FlaskJsonResponseType
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestFlaskJsonResponseType(BaseIntegrationTest):
    codemod = FlaskJsonResponseType
    code_path = "tests/samples/flask_json_response_type.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (
                8,
                """    return make_response(json_response, {'Content-Type': 'application/json'})\n""",
            ),
        ],
    )

    # fmt: off
    expected_diff =(
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
    change_description = FlaskJsonResponseType.CHANGE_DESCRIPTION
    num_changed_files = 1
