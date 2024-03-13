from codemodder.codemods.sonar import SonarCodemod
from core_codemods.django_json_response_type import DjangoJsonResponseType

SonarDjangoJsonResponseType = SonarCodemod.from_core_codemod(
    name="django-json-response-type-S5131",
    other=DjangoJsonResponseType,
    rule_id="pythonsecurity:S5131",
    rule_name="Endpoints should not be vulnerable to reflected XSS attacks (Django)",
    rule_url="https://rules.sonarsource.com/python/type/Bug/RSPEC-5131/",
)
