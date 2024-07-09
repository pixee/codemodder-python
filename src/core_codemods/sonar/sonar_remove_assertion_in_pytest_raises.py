from core_codemods.remove_assertion_in_pytest_raises import (
    RemoveAssertionInPytestRaises,
)
from core_codemods.sonar.api import SonarCodemod

SonarRemoveAssertionInPytestRaises = SonarCodemod.from_core_codemod(
    name="remove-assertion-in-pytest-raises",
    other=RemoveAssertionInPytestRaises,
    rule_id="python:S5915",
    rule_name="Assertions should not be made at the end of blocks expecting an exception",
)
