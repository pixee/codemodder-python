from core_codemods.fix_assert_tuple import FixAssertTuple
from core_codemods.sonar.api import SonarCodemod

SonarFixAssertTuple = SonarCodemod.from_core_codemod(
    name="fix-assert-tuple",
    other=FixAssertTuple,
    rule_id="python:S5905",
    rule_name="Assert should not be called on a tuple literal",
)
