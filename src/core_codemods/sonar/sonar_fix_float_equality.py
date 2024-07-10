from core_codemods.fix_float_equality import FixFloatEquality
from core_codemods.sonar.api import SonarCodemod

SonarFixFloatEquality = SonarCodemod.from_core_codemod(
    name="fix-float-equality",
    other=FixFloatEquality,
    rule_id="python:S1244",
    rule_name="Floating point numbers should not be tested for equality",
)
