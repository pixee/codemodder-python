from core_codemods.django_receiver_on_top import DjangoReceiverOnTop
from tests.codemods.base_codemod_test import BaseCodemodTest
from textwrap import dedent


class TestDjangoReceiverOnTop(BaseCodemodTest):
    codemod = DjangoReceiverOnTop

    def test_name(self):
        assert self.codemod.name() == "django-receiver-on-top"

    def test_simple(self, tmpdir):
        input_code = """\
        from django.dispatch import receiver

        @csrf_exempt
        @receiver(request_finished)
        def foo():
            pass
        """
        expected = """\
        from django.dispatch import receiver

        @receiver(request_finished)
        @csrf_exempt
        def foo():
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_simple_alias(self, tmpdir):
        input_code = """\
        from django.dispatch import receiver as rec

        @csrf_exempt
        @rec(request_finished)
        def foo():
            pass
        """
        expected = """\
        from django.dispatch import receiver as rec

        @rec(request_finished)
        @csrf_exempt
        def foo():
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_no_receiver(self, tmpdir):
        input_code = """\
        @csrf_exempt
        def foo():
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_receiver_but_not_djangos(self, tmpdir):
        input_code = """\
        from not_django import receiver

        @csrf_exempt
        @receiver(request_finished)
        def foo():
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_receiver_on_top(self, tmpdir):
        input_code = """\
        from django.dispatch import receiver

        @receiver(request_finished)
        @csrf_exempt
        def foo():
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0
