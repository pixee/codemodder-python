from codemodder.codemods.test.integration_utils import BaseIntegrationTest
from core_codemods.break_or_continue_out_of_loop import (
    BreakOrContinueOutOfLoop,
    BreakOrContinueOutOfLoopTransformer,
)


class TestBreakOrContinueOutOfLoop(BaseIntegrationTest):
    codemod = BreakOrContinueOutOfLoop
    original_code = """
    def f():
        continue
    """
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
