from codemodder.codemods.base_codemod import Reference
from codemodder.codemods.sonar import SonarCodemod
from core_codemods.literal_or_new_object_identity import LiteralOrNewObjectIdentity

SonarLiteralOrNewObjectIdentity = SonarCodemod.from_core_codemod(
    name="literal-or-new-object-identity-S5796",
    other=LiteralOrNewObjectIdentity,
    rules=["python:S5796"],
    new_references=[
        Reference(url="https://rules.sonarsource.com/python/type/Bug/RSPEC-5796/"),
    ],
)
