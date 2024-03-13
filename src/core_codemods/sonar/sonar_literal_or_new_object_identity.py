from codemodder.codemods.sonar import SonarCodemod
from core_codemods.literal_or_new_object_identity import LiteralOrNewObjectIdentity

SonarLiteralOrNewObjectIdentity = SonarCodemod.from_core_codemod(
    name="literal-or-new-object-identity-S5796",
    other=LiteralOrNewObjectIdentity,
    rule_id="python:S5796",
    rule_name="New objects should not be created only to check their identity",
    rule_url="https://rules.sonarsource.com/python/type/Bug/RSPEC-5796/",
)
