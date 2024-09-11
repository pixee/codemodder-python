from core_codemods.process_creation_sandbox import ProcessSandbox
from core_codemods.sonar.api import SonarCodemod

SonarSandboxProcessCreation = SonarCodemod.from_core_codemod(
    name="sandbox-process-creation",
    other=ProcessSandbox(),
    rule_id="pythonsecurity:S2076",
    rule_name="OS commands should not be vulnerable to command injection attacks",
)
