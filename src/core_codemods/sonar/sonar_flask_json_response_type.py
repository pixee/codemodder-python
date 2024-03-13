from codemodder.codemods.sonar import SonarCodemod
from core_codemods.flask_json_response_type import FlaskJsonResponseType

SonarFlaskJsonResponseType = SonarCodemod.from_core_codemod(
    name="flask-json-response-type-S5131",
    other=FlaskJsonResponseType,
    rule_id="pythonsecurity:S5131",
    rule_name="Endpoints should not be vulnerable to reflected XSS attacks (Flask)",
    rule_url="https://rules.sonarsource.com/python/type/Bug/RSPEC-5131/",
)
