import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_django_model_without_dunder_str import (
    SonarDjangoModelWithoutDunderStr,
)


class TestSonarDjangoModelWithoutDunderStr(BaseSASTCodemodTest):
    codemod = SonarDjangoModelWithoutDunderStr
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "django-model-without-dunder-str"
        assert self.codemod.id == "sonar:python/django-model-without-dunder-str"

    def test_simple(self, tmpdir):
        input_code = """\
        from django.db import models
                
        class User(models.Model):
            name = models.CharField(max_length=100)
            phone = models.IntegerField(blank=True)
        """
        expected = """\
        from django.db import models
                
        class User(models.Model):
            name = models.CharField(max_length=100)
            phone = models.IntegerField(blank=True)
            
            def __str__(self):
                model_name = self.__class__.__name__
                fields_str = ", ".join((f"{field.name}={getattr(self, field.name)}" for field in self._meta.fields))
                return f"{model_name}({fields_str})"
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S6554",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 3,
                        "endLine": 3,
                        "startOffset": 6,
                        "endOffset": 10,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
