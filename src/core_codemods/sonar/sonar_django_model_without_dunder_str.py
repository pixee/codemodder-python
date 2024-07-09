from core_codemods.django_model_without_dunder_str import DjangoModelWithoutDunderStr
from core_codemods.sonar.api import SonarCodemod

SonarDjangoModelWithoutDunderStr = SonarCodemod.from_core_codemod(
    name="django-model-without-dunder-str",
    other=DjangoModelWithoutDunderStr,
    rule_id="python:S6554",
    rule_name='Django models should define a "__str__" method',
)
