import pytest
from core_codemods.fix_task_instantiation import FixTaskInstantiation
from tests.codemods.base_codemod_test import BaseCodemodTest


class TestFixTaskInstantiation(BaseCodemodTest):
    codemod = FixTaskInstantiation

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                import asyncio
                asyncio.Task(coro(1, 2))
                """,
                """
                import asyncio
                asyncio.create_task(coro(1, 2))
                """,
            ),
            (
                """
                import asyncio
                async def coro(*args):
                    print(args)

                my_coro = coro(1, 2)
                asyncio.Task(my_coro)
                """,
                """
                import asyncio
                async def coro(*args):
                    print(args)

                my_coro = coro(1, 2)
                asyncio.create_task(my_coro)
                """,
            ),
            (
                """
                import asyncio
                my_loop = asyncio.get_event_loop()
                asyncio.Task(coro(1, 2), loop=my_loop)
                """,
                """
                import asyncio
                my_loop = asyncio.get_event_loop()
                my_loop.create_task(coro(1, 2))
                """,
            ),
        ],
    )
    def test_import(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                from asyncio import Task
                Task(coro(1, 2))
                """,
                """
                import asyncio

                asyncio.create_task(coro(1, 2))
                """,
            ),
            (
                """
                from asyncio import Task, get_event_loop
                my_loop = get_event_loop()
                Task(coro(1, 2), loop=my_loop)
                """,
                """
                from asyncio import get_event_loop
                my_loop = get_event_loop()
                my_loop.create_task(coro(1, 2))
                """,
            ),
        ],
    )
    def test_from_import(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                from asyncio import Task as taskInit
                taskInit(coro(1, 2))
                """,
                """
                import asyncio

                asyncio.create_task(coro(1, 2))
                """,
            ),
            (
                """
                from asyncio import get_event_loop, Task as taskInit
                my_loop = get_event_loop()
                taskInit(coro(1, 2), loop=my_loop)
                """,
                """
                from asyncio import get_event_loop
                my_loop = get_event_loop()
                my_loop.create_task(coro(1, 2))
                """,
            ),
        ],
    )
    def test_import_alias(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                import asyncio
                asyncio.Task(coro(1, 2), name='task', eager_start=True)
                """,
                """
                import asyncio
                asyncio.create_task(coro(1, 2), name='task', eager_start=True)
                """,
            ),
            (
                """
                import asyncio
                my_loop = asyncio.get_event_loop()
                asyncio.Task(coro(1, 2), name='task', loop=my_loop, context=None)
                """,
                """
                import asyncio
                my_loop = asyncio.get_event_loop()
                my_loop.create_task(coro(1, 2), name='task', context=None)
                """,
            ),
        ],
    )
    def test_with_other_kwargs(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("loop_value", ["None", "True", '"gibberish"', 10])
    def test_loop_kwarg_variations(self, tmpdir, loop_value):
        input_code = (
            output_code
        ) = f"""
        import asyncio
        asyncio.Task(coro(1, 2), loop={loop_value})
        """
        if loop_value == "None":
            output_code = """
            import asyncio
            asyncio.create_task(coro(1, 2), loop=None)
            """
        self.run_and_assert(tmpdir, input_code, output_code)

    def test_asyncio_script(self, tmpdir):
        input_code = """
        import asyncio

        async def my_coroutine():
            await asyncio.sleep(1)
            print("Task completed")
        
        async def main():
            loop = asyncio.get_running_loop()
            task = asyncio.Task(my_coroutine(), loop=loop)
            await task
            task_2 = asyncio.Task(my_coroutine())
            await task_2        
        asyncio.run(main())
        """
        output_code = """
        import asyncio

        async def my_coroutine():
            await asyncio.sleep(1)
            print("Task completed")
        
        async def main():
            loop = asyncio.get_running_loop()
            task = loop.create_task(my_coroutine())
            await task
            task_2 = asyncio.create_task(my_coroutine())
            await task_2        
        asyncio.run(main())
        """
        self.run_and_assert(tmpdir, input_code, output_code, num_changes=2)
