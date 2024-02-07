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

    # @pytest.mark.parametrize(
    #     "code",
    #     [
    #         """
    #     import xyz
    #     xyz.warn('something')
    #     """,
    #         """
    #     import my_logging
    #     log = my_logging.getLogger('anything')
    #     log.warn('something')
    #     """,
    #     ],
    # )
    # def test_different_warn(self, tmpdir, code):
    #     self.run_and_assert(tmpdir, code, code)
    #
    # @pytest.mark.xfail(reason="Not currently supported")
    # def test_log_as_arg(self, tmpdir):
    #     code = """
    #     import logging
    #     log = logging.getLogger('foo')
    #     def some_function(logger):
    #         logger.{}("hi")
    #     some_function(log)
    #     """
    #     original_code = code.format("warn")
    #     new_code = code.format("warning")
    #     self.run_and_assert(tmpdir, original_code, new_code)
