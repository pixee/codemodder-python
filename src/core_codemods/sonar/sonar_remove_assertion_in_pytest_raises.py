from codemodder.codemods.base_codemod import Reference
from codemodder.codemods.sonar import SonarCodemod
from core_codemods.remove_assertion_in_pytest_raises import (
    RemoveAssertionInPytestRaises,
)

SonarRemoveAssertionInPytestRaises = SonarCodemod.from_core_codemod(
    name="remove-assertion-in-pytest-raises-S5915",
    other=RemoveAssertionInPytestRaises,
    rules=["python:S5915"],
    new_references=[
        Reference(url="https://rules.sonarsource.com/python/type/Bug/RSPEC-5915/"),
    ],
)
