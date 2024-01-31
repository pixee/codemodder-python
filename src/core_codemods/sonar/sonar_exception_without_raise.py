from codemodder.codemods.base_codemod import Reference
from codemodder.codemods.sonar import SonarCodemod
from core_codemods.exception_without_raise import ExceptionWithoutRaise

SonarExceptionWithoutRaise = SonarCodemod.from_core_codemod(
    name="exception-without-raise-S3984",
    other=ExceptionWithoutRaise,
    rules=["python:S3984"],
    new_references=[
        Reference(url="https://rules.sonarsource.com/python/type/Bug/RSPEC-3984/"),
    ],
)
