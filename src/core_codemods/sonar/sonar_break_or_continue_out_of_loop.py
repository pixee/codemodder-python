from core_codemods.break_or_continue_out_of_loop import BreakOrContinueOutOfLoop
from core_codemods.sonar.api import SonarCodemod

SonarBreakOrContinueOutOfLoop = SonarCodemod.from_core_codemod(
    name="break-or-continue-out-of-loop",
    other=BreakOrContinueOutOfLoop,
    rule_id="python:S1716",
    rule_name='"break" and "continue" should not be used outside a loop',
)
