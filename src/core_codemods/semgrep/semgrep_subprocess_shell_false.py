from codemodder.codemods.base_codemod import ToolRule
from core_codemods.semgrep.api import SemgrepCodemod, semgrep_url_from_id
from core_codemods.subprocess_shell_false import SubprocessShellFalse

SemgrepSubprocessShellFalse = SemgrepCodemod.from_core_codemod(
    name="subprocess-shell-false",
    other=SubprocessShellFalse,
    rules=[
        ToolRule(
            id=(
                rule_id := "python.lang.security.audit.subprocess-shell-true.subprocess-shell-true"
            ),
            name="subprocess-shell-true",
            url=semgrep_url_from_id(rule_id),
        )
    ],
)
