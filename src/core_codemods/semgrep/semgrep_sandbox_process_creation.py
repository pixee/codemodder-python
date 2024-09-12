from core_codemods.process_creation_sandbox import ProcessSandbox
from core_codemods.semgrep.api import SemgrepCodemod, ToolRule, semgrep_url_from_id

SemgrepSandboxProcessCreation = SemgrepCodemod.from_core_codemod(
    name="sandbox-process-creation",
    other=ProcessSandbox(),
    rules=[
        ToolRule(
            id=(
                rule_id := "python.lang.security.dangerous-system-call.dangerous-system-call"
            ),
            name="dangerous-system-call",
            url=semgrep_url_from_id(rule_id),
        ),
    ],
)
