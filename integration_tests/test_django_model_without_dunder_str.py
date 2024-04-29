from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.django_model_without_dunder_str import (
    DjangoModelWithoutDunderStr,
    DjangoModelWithoutDunderStrTransformer,
)


class TestDjangoModelWithoutDunderStr(BaseIntegrationTest):
    codemod = DjangoModelWithoutDunderStr
    original_code = """
    import django
    from django.conf import settings
    from django.db import models
    # required to run this module standalone for testing
    if not settings.configured:
        settings.configure()
    django.setup()
    
    
    class Message(models.Model):
        author = models.CharField(max_length=100)
        content = models.CharField(max_length=200)
        class Meta:
            app_label = 'myapp'

    """
    replacement_lines = [
        (16, """\n"""),
        (17, """    def __str__(self):\n"""),
        (18, """        model_name = self.__class__.__name__\n"""),
        (
            19,
            """        fields_str = ", ".join((f"{field.name}={getattr(self, field.name)}" for field in self._meta.fields))\n""",
        ),
        (20, """        return f"{model_name}({fields_str})"\n"""),
    ]

    # fmt: off
    expected_diff = (
    """--- \n"""
    """+++ \n"""
    """@@ -12,3 +12,8 @@\n"""
    """     content = models.CharField(max_length=200)\n"""
    """     class Meta:\n"""
    """         app_label = 'myapp'\n"""
    """+\n"""
    """+    def __str__(self):\n"""
    """+        model_name = self.__class__.__name__\n"""
    """+        fields_str = ", ".join((f"{field.name}={getattr(self, field.name)}" for field in self._meta.fields))\n"""
    """+        return f"{model_name}({fields_str})"\n"""
    )
    # fmt: on

    expected_line_change = "10"
    change_description = DjangoModelWithoutDunderStrTransformer.change_description
    num_changed_files = 1

    def check_code_after(self):
        """Executes models.py and instantiates the model to ensure expected str representation"""
        module = super().check_code_after()
        inst = module.Message(pk=1, author="name", content="content")
        assert str(inst) == "Message(id=1, author=name, content=content)"
