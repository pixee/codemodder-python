from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.django_json_response_type import DjangoJsonResponseTypeTransformer
from core_codemods.sonar.sonar_django_json_response_type import (
    SonarDjangoJsonResponseType,
)


class TestSonarDjangoJsonResponseType(SonarIntegrationTest):
    codemod = SonarDjangoJsonResponseType
    code_path = "tests/samples/django_json_response_type.py"
    replacement_lines = [
        (
            6,
            """    return HttpResponse(json_response, content_type="application/json")\n""",
        ),
    ]

    # fmt: off
    expected_diff = (
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
