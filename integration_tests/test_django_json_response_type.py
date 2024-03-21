from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.django_json_response_type import (
    DjangoJsonResponseType,
    DjangoJsonResponseTypeTransformer,
)


class TestDjangoJsonResponseType(BaseIntegrationTest):
    codemod = DjangoJsonResponseType
    original_code = """
    from django.http import HttpResponse
    import json
    
    def foo(request):
        json_response = json.dumps({ "user_input": request.GET.get("input") })
        return HttpResponse(json_response)
    """
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
