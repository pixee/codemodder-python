from codemodder.codemods.sonar import SonarCodemod
from core_codemods.fix_assert_tuple import FixAssertTuple

SonarFixAssertTuple = SonarCodemod.from_core_codemod(
    name="fix-assert-tuple-S5905",
    other=FixAssertTuple,
    rule_id="python:S5905",
    rule_name="Assert should not be called on a tuple literal",
    rule_url="https://rules.sonarsource.com/python/type/Bug/RSPEC-5905/",
)
