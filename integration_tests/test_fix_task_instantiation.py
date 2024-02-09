from core_codemods.fix_task_instantiation import FixTaskInstantiation
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestFixTaskInstantiation(BaseIntegrationTest):
    codemod = FixTaskInstantiation
    code_path = "tests/samples/fix_task_instantiation.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (
                7,
                """    task = asyncio.create_task(my_coroutine(), name="my task")\n""",
            ),
        ],
    )

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -5,7 +5,7 @@\n"""
    """     print("Task completed")\n"""
    """ \n"""
    """ async def main():\n"""
    """-    task = asyncio.Task(my_coroutine(), name="my task")\n"""
    """+    task = asyncio.create_task(my_coroutine(), name="my task")\n"""
    """     await task\n"""
    """ \n"""
    """ asyncio.run(main())\n"""
    )
    # fmt: on

    expected_line_change = "8"
    change_description = FixTaskInstantiation.change_description
    num_changed_files = 1
