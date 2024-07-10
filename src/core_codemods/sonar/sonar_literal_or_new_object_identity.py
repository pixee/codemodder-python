from core_codemods.literal_or_new_object_identity import LiteralOrNewObjectIdentity
from core_codemods.sonar.api import SonarCodemod

SonarLiteralOrNewObjectIdentity = SonarCodemod.from_core_codemod(
    name="literal-or-new-object-identity",
    other=LiteralOrNewObjectIdentity,
    rule_id="python:S5796",
    rule_name="New objects should not be created only to check their identity",
)
