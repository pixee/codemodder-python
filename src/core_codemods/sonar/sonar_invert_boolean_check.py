from core_codemods.invert_boolean_check import InvertedBooleanCheck
from core_codemods.sonar.api import SonarCodemod

SonarInvertedBooleanCheck = SonarCodemod.from_core_codemod(
    name="invert-boolean-check",
    other=InvertedBooleanCheck,
    rule_id="python:S1940",
    rule_name="Boolean checks should not be inverted",
)
