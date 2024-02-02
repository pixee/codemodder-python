from core_codemods.flask_json_response_type import FlaskJsonResponseTypeTransformer
from core_codemods.sonar.sonar_flask_json_response_type import (
    SonarFlaskJsonResponseType,
)
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestSonarFlaskJsonResponseType(BaseIntegrationTest):
    codemod = SonarFlaskJsonResponseType
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
    sonar_issues_json = "tests/samples/sonar_issues.json"

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
    change_description = FlaskJsonResponseTypeTransformer.change_description
    num_changed_files = 1
