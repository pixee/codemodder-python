from core_codemods.django_json_response_type import DjangoJsonResponseType
from core_codemods.sonar.api import SonarCodemod

SonarDjangoJsonResponseType = SonarCodemod.from_core_codemod(
    name="django-json-response-type",
    other=DjangoJsonResponseType,
    rule_id="pythonsecurity:S5131",
    rule_name="Endpoints should not be vulnerable to reflected XSS attacks (Django)",
)
