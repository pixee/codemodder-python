from core_codemods.semgrep.api import SemgrepCodemod
from core_codemods.subprocess_shell_false import SubprocessShellFalse

SemgrepSubprocessShellFalse = SemgrepCodemod.from_core_codemod(
    name="subprocess-shell-false",
    other=SubprocessShellFalse,
    rule_id="python.lang.security.audit.subprocess-shell-true.subprocess-shell-true",
    rule_name="subprocess-shell-true",
)
