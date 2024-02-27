from core_codemods.fix_async_task_instantiation import FixAsyncTaskInstantiation
from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestFixAsyncTaskInstantiation(BaseIntegrationTest):
    codemod = FixAsyncTaskInstantiation
    code_path = "tests/samples/fix_async_task_instantiation.py"
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
    change_description = FixAsyncTaskInstantiation.change_description
    num_changed_files = 1
