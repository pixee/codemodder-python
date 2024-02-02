from codemodder.codemods.base_codemod import Reference
from codemodder.codemods.sonar import SonarCodemod
from core_codemods.flask_json_response_type import FlaskJsonResponseType

SonarFlaskJsonResponseType = SonarCodemod.from_core_codemod(
    name="flask-json-response-type-S5131",
    other=FlaskJsonResponseType,
    rules=["pythonsecurity:S5131"],
    new_references=[
        Reference(url="https://rules.sonarsource.com/python/type/Bug/RSPEC-5131/"),
    ],
)
