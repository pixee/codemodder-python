from core_codemods.exception_without_raise import ExceptionWithoutRaise
from core_codemods.sonar.api import SonarCodemod

SonarExceptionWithoutRaise = SonarCodemod.from_core_codemod(
    name="exception-without-raise-S3984",
    other=ExceptionWithoutRaise,
    rule_id="python:S3984",
    rule_name="Exceptions should not be created without being raised",
    rule_url="https://rules.sonarsource.com/python/type/Bug/RSPEC-3984/",
)
