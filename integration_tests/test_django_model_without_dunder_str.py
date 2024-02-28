from core_codemods.django_model_without_dunder_str import (
    DjangoModelWithoutDunderStr,
    DjangoModelWithoutDunderStrTransformer,
)
from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestDjangoModelWithoutDunderStr(BaseIntegrationTest):
    codemod = DjangoModelWithoutDunderStr
    code_path = "tests/samples/django-project/mysite/mysite/models.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (15, """\n"""),
            (16, """    def __str__(self):\n"""),
            (17, """        model_name = self.__class__.__name__\n"""),
            (
                18,
                """        fields_str = ", ".join((f"{field.name}={getattr(self, field.name)}" for field in self._meta.fields))\n""",
            ),
            (19, """        return f"{model_name}({fields_str})"\n"""),
        ],
    )

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -11,3 +11,8 @@\n"""
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

    expected_line_change = "9"
    change_description = DjangoModelWithoutDunderStrTransformer.change_description
    num_changed_files = 1

    def check_code_after(self):
        """Executes models.py and instantiates the model to ensure expected str representation"""
        module = super().check_code_after()
        inst = module.Message(pk=1, author="name", content="content")
        assert str(inst) == "Message(id=1, author=name, content=content)"
