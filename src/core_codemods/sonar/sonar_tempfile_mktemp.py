from core_codemods.sonar.api import SonarCodemod
from core_codemods.tempfile_mktemp import TempfileMktemp

SonarTempfileMktemp = SonarCodemod.from_core_codemod(
    name="secure-tempfile",
    other=TempfileMktemp,
    rule_id="python:S5445",
    rule_name="Insecure temporary file creation methods should not be used",
)
