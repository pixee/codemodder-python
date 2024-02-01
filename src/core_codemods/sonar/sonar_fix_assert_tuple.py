from codemodder.codemods.base_codemod import Reference
from codemodder.codemods.sonar import SonarCodemod
from core_codemods.fix_assert_tuple import FixAssertTuple

SonarFixAssertTuple = SonarCodemod.from_core_codemod(
    name="fix-assert-tuple-S5905",
    other=FixAssertTuple,
    rules=["python:S5905"],
    new_references=[
        Reference(url="https://rules.sonarsource.com/python/type/Bug/RSPEC-5905/"),
    ],
)
