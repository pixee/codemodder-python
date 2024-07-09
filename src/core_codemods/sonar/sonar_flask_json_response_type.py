from core_codemods.flask_json_response_type import FlaskJsonResponseType
from core_codemods.sonar.api import SonarCodemod

SonarFlaskJsonResponseType = SonarCodemod.from_core_codemod(
    name="flask-json-response-type",
    other=FlaskJsonResponseType,
    rule_id="pythonsecurity:S5131",
    rule_name="Endpoints should not be vulnerable to reflected XSS attacks (Flask)",
)
