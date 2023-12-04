from core_codemods.django_json_response_type import DjangoJsonResponseType
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest
from textwrap import dedent


class TestDjangoJsonResponseType(BaseSemgrepCodemodTest):
    codemod = DjangoJsonResponseType

    def test_name(self):
        assert self.codemod.name() == "django-json-response-type"

    def test_simple(self, tmpdir):
        input_code = """\
        from django.http import HttpResponse
        import json

        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return HttpResponse(json_response)
        """
        expected = """\
        from django.http import HttpResponse
        import json

        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return HttpResponse(json_response, content_type="application/json")
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_alias(self, tmpdir):
        input_code = """\
        from django.http import HttpResponse as response
        import json as jsan

        def foo(request):
            json_response = jsan.dumps({ "user_input": request.GET.get("input") })
            return response(json_response)
        """
        expected = """\
        from django.http import HttpResponse as response
        import json as jsan

        def foo(request):
            json_response = jsan.dumps({ "user_input": request.GET.get("input") })
            return response(json_response, content_type="application/json")
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_direct(self, tmpdir):
        input_code = """\
        from django.http import HttpResponse
        import json

        def foo(request):
            return HttpResponse(json.dumps({ "user_input": request.GET.get("input") }))
        """
        expected = """\
        from django.http import HttpResponse
        import json

        def foo(request):
            return HttpResponse(json.dumps({ "user_input": request.GET.get("input") }), content_type="application/json")
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_content_type_set(self, tmpdir):
        input_code = """\
        from django.http import HttpResponse
        import json

        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return HttpResponse(json_response, content_type='application/json')
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_no_json_input(self, tmpdir):
        input_code = """\
        from django.http import HttpResponse
        import json

        def foo(request):
            dict_reponse = { "user_input": request.GET.get("input") }
            return HttpResponse(dict_response)
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0
