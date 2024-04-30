from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.django_model_without_dunder_str import (
    DjangoModelWithoutDunderStrTransformer,
)
from core_codemods.sonar.sonar_django_model_without_dunder_str import (
    SonarDjangoModelWithoutDunderStr,
)


class TestSonarDjangoModelWithoutDunderStr(SonarIntegrationTest):
    codemod = SonarDjangoModelWithoutDunderStr
    code_path = "tests/samples/django_model.py"
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
    """@@ -13,3 +13,8 @@\n"""
    """     phone = models.IntegerField(blank=True)\n"""
    """     class Meta:\n"""
    """         app_label = 'myapp'\n"""
    """+\n"""
    """+    def __str__(self):\n"""
    """+        model_name = self.__class__.__name__\n"""
    """+        fields_str = ", ".join((f"{field.name}={getattr(self, field.name)}" for field in self._meta.fields))\n"""
    """+        return f"{model_name}({fields_str})"\n"""
    )
    # fmt: on

    expected_line_change = "11"
    change_description = DjangoModelWithoutDunderStrTransformer.change_description
    num_changed_files = 1
