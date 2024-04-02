from codemodder.codemods.sonar import SonarCodemod
from core_codemods.tempfile_mktemp import TempfileMktemp

SonarTempfileMktemp = SonarCodemod.from_core_codemod(
    name="secure-tempfile-S5445",
    other=TempfileMktemp,
    rule_id="python:S5445",
    rule_name="Insecure temporary file creation methods should not be used",
    rule_url="https://rules.sonarsource.com/python/type/Vulnerability/RSPEC-5445/",
)
