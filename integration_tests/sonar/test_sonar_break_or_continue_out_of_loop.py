from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.break_or_continue_out_of_loop import (
    BreakOrContinueOutOfLoopTransformer,
)
from core_codemods.sonar.sonar_break_or_continue_out_of_loop import (
    SonarBreakOrContinueOutOfLoop,
)


class TestSonarSQLParameterization(SonarIntegrationTest):
    codemod = SonarBreakOrContinueOutOfLoop
    code_path = "tests/samples/break_or_continue_out_of_loop.py"
    replacement_lines = [
        (2, """    pass\n"""),
    ]

    # fmt: off
    expected_diff = (
    """--- \n"""
    """+++ \n"""
    """@@ -1,2 +1,2 @@\n"""
    """ def f():\n"""
    """-    continue\n"""
    """+    pass\n"""
    )
    # fmt: on

    expected_line_change = "2"
    change_description = BreakOrContinueOutOfLoopTransformer.change_description
    num_changed_files = 1
