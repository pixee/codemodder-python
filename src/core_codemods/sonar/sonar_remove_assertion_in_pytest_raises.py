from codemodder.codemods.sonar import SonarCodemod
from core_codemods.remove_assertion_in_pytest_raises import (
    RemoveAssertionInPytestRaises,
)

SonarRemoveAssertionInPytestRaises = SonarCodemod.from_core_codemod(
    name="remove-assertion-in-pytest-raises-S5915",
    other=RemoveAssertionInPytestRaises,
    rule_id="python:S5915",
    rule_name="Assertions should not be made at the end of blocks expecting an exception",
    rule_url="https://rules.sonarsource.com/python/type/Bug/RSPEC-5915/",
)
