from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.fix_async_task_instantiation import FixAsyncTaskInstantiation


class TestFixAsyncTaskInstantiation(BaseIntegrationTest):
    codemod = FixAsyncTaskInstantiation
    original_code = """
    import asyncio

    async def my_coroutine():
        await asyncio.sleep(1)
        print("Task completed")
    
    async def main():
        task = asyncio.Task(my_coroutine(), name="my task")
        await task
    
    asyncio.run(main())
    """
    replacement_lines = [
        (
            8,
            """    task = asyncio.create_task(my_coroutine(), name="my task")\n""",
        ),
    ]
    # fmt: off
    expected_diff = (
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
