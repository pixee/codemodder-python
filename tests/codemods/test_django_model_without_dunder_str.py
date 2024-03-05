from codemodder.codemods.test import BaseCodemodTest
from core_codemods.django_model_without_dunder_str import DjangoModelWithoutDunderStr


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
                model_name = self.__class__.__name__
                fields_str = ", ".join((f"{field.name}={getattr(self, field.name)}" for field in self._meta.fields))
                return f"{model_name}({fields_str})"

        def something():
            pass
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_model_inherits_dunder_str(self, tmpdir):
        input_code = """
        from django.db import models

        class Custom:
            def __str__(self):
                pass
                        
        class User(Custom, models.Model):
            name = models.CharField(max_length=100)
            phone = models.IntegerField(blank=True)

        def something():
            pass
        """
        self.run_and_assert(tmpdir, input_code, input_code)
