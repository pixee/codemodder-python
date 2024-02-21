from core_codemods.django_model_without_dunder_str import DjangoModelWithoutDunderStr
from tests.codemods.base_codemod_test import BaseCodemodTest


class TestDjangoModelWithoutDunderStr(BaseCodemodTest):
    codemod = DjangoModelWithoutDunderStr

    def test_name(self):
        assert self.codemod.name == "django-model-without-dunder-str"

    def test_no_change(self, tmpdir):
        input_code = """
        from django.db import models

        class User(models.Model):
            name = models.CharField(max_length=100)
            phone = models.IntegerField(blank=True)

            def __str__(self):
                return "doesntmatter"
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_no_dunder_str(self, tmpdir):
        input_code = """
        from django.db import models

        class User(models.Model):
            name = models.CharField(max_length=100)
            phone = models.IntegerField(blank=True)
            
            @property
            def decorated_name(self):
                return f"***{self.name}***"

        def something():
            pass
        """
        expected = """
        from django.db import models

        class User(models.Model):
            name = models.CharField(max_length=100)
            phone = models.IntegerField(blank=True)

            @property
            def decorated_name(self):
                return f"***{self.name}***"

            def __str__(self):
                pass

        def something():
            pass
        """
        self.run_and_assert(tmpdir, input_code, expected)

    # def test_simple_alias(self, tmpdir):
    #     input_code = """
    #     from django.dispatch import receiver as rec
    #
    #     @csrf_exempt
    #     @rec(request_finished)
    #     def foo():
    #         pass
    #     """
    #     expected = """
    #     from django.dispatch import receiver as rec
    #
    #     @rec(request_finished)
    #     @csrf_exempt
    #     def foo():
    #         pass
    #     """
    #     self.run_and_assert(tmpdir, input_code, expected)
    #
    # def test_no_receiver(self, tmpdir):
    #     input_code = """
    #     @csrf_exempt
    #     def foo():
    #         pass
    #     """
    #     self.run_and_assert(tmpdir, input_code, input_code)
    #
    # def test_receiver_but_not_djangos(self, tmpdir):
    #     input_code = """
    #     from not_django import receiver
    #
    #     @csrf_exempt
    #     @receiver(request_finished)
    #     def foo():
    #         pass
    #     """
    #     self.run_and_assert(tmpdir, input_code, input_code)
    #
    # def test_receiver_on_top(self, tmpdir):
    #     input_code = """
    #     from django.dispatch import receiver
    #
    #     @receiver(request_finished)
    #     @csrf_exempt
    #     def foo():
    #         pass
    #     """
    #     self.run_and_assert(tmpdir, input_code, input_code)
