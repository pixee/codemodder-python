from core_codemods.django_json_response_type import DjangoJsonResponseTypeTransformer
from core_codemods.sonar.sonar_django_json_response_type import (
    SonarDjangoJsonResponseType,
)
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestSonarDjangoJsonResponseType(BaseIntegrationTest):
    codemod = SonarDjangoJsonResponseType
    code_path = "tests/samples/django_json_response_type.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (
                5,
                """    return HttpResponse(json_response, content_type="application/json")\n""",
            ),
        ],
    )
    sonar_issues_json = "tests/samples/sonar_issues.json"

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -3,4 +3,4 @@\n"""
    """ \n"""
    """ def foo(request):\n"""
    """     json_response = json.dumps({ "user_input": request.GET.get("input") })\n"""
    """-    return HttpResponse(json_response)\n"""
    """+    return HttpResponse(json_response, content_type="application/json")\n"""
    )
    # fmt: on

    expected_line_change = "6"
    change_description = DjangoJsonResponseTypeTransformer.change_description
    num_changed_files = 1
