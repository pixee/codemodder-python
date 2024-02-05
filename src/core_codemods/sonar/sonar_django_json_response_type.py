from codemodder.codemods.base_codemod import Reference
from codemodder.codemods.sonar import SonarCodemod
from core_codemods.django_json_response_type import DjangoJsonResponseType

SonarDjangoJsonResponseType = SonarCodemod.from_core_codemod(
    name="django-json-response-type-S5131",
    other=DjangoJsonResponseType,
    rules=["pythonsecurity:S5131"],
    new_references=[
        Reference(url="https://rules.sonarsource.com/python/type/Bug/RSPEC-5131/"),
    ],
)
