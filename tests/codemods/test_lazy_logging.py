import pytest
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest
from core_codemods.lazy_logging import LazyLogging

each_func = pytest.mark.parametrize("func", LazyLogging.logging_funcs)


class TestLazyLogging(BaseSemgrepCodemodTest):
    codemod = LazyLogging

    def test_name(self):
        assert self.codemod.name == "lazy-logging"

    @each_func
    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """\
            import logging
            e = "error"
            logging.{}("Error occurred: %s" % e)
            """,
                """\
            import logging
            e = "error"
            logging.{}("Error occurred: %s", e)
            """,
            ),
            (
                """\
            import logging
            logging.{}("Error occurred: %s" % ("one",))
            """,
                """\
            import logging
            logging.{}("Error occurred: %s", "one")
            """,
            ),
            (
                """\
            import logging
            log = logging.getLogger('anything')
            log.{}("one: %s, two: %s" % ("one", "two"))
            """,
                """\
            import logging
            log = logging.getLogger('anything')
            log.{}("one: %s, two: %s", "one", "two")
            """,
            ),
        ],
    )
    def test_import(self, tmpdir, input_code, expected_output, func):
        self.run_and_assert(
            tmpdir, input_code.format(func), expected_output.format(func)
        )

    @each_func
    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """\
            from logging import {0}
            e = "error"
            {0}("Error occurred: %s" % e)
            """,
                """\
            from logging import {0}
            e = "error"
            {0}("Error occurred: %s", e)
            """,
            ),
            (
                """\
            from logging import getLogger
            getLogger('anything').{}("one: %s, two: %s" % ("one", "two"))
            """,
                """\
            from logging import getLogger
            getLogger('anything').{}("one: %s, two: %s", "one", "two")
            """,
            ),
        ],
    )
    def test_from_import(self, tmpdir, input_code, expected_output, func):
        self.run_and_assert(
            tmpdir, input_code.format(func), expected_output.format(func)
        )

    @each_func
    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """\
            from logging import {} as log_func
            e = "error"
            log_func("Error occurred: %s" % e)
            """,
                """\
            from logging import {} as log_func
            e = "error"
            log_func("Error occurred: %s", e)
            """,
            ),
            (
                """\
            from logging import getLogger as make_logger
            make_logger('anything').{}("one: %s, two: %s" % ("one", "two"))
            """,
                """\
            from logging import getLogger as make_logger
            make_logger('anything').{}("one: %s, two: %s", "one", "two")
            """,
            ),
        ],
    )
    def test_import_alias(self, tmpdir, input_code, expected_output, func):
        self.run_and_assert(
            tmpdir, input_code.format(func), expected_output.format(func)
        )

    @pytest.mark.parametrize(
        "code",
        [
            """
        import xyz
        xyz.info.("hi: %s" % 'hello')
        """,
            """
        import my_logging
        log = my_logging.getLogger('anything')
        log.info.("hi: %s" % 'hello')
        """,
        ],
    )
    def test_different_log_func(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)

    # @pytest.mark.xfail(reason="Not currently supported")
    # def test_log_as_arg(self, tmpdir):
    #     code = """\
    #     import logging
    #     log = logging.getLogger('foo')
    #     def some_function(logger):
    #         logger.{}("hi")
    #     some_function(log)
    #     """
    #     original_code = code.format("warn")
    #     new_code = code.format("warning")
    #     self.run_and_assert(tmpdir, original_code, new_code)

    # @pytest.mark.parametrize(
    #     "code",
    #     [
    #         "x.startswith('foo')",
    #         "x.startswith(('f', 'foo'))",
    #         "x.startswith('foo') and x.startswith('f')",
    #         "x.startswith('foo') and x.startswith('f') or True",
    #         "x.startswith('foo') or x.endswith('f')",
    #         "x.startswith('foo') or y.startswith('f')",
    #     ],
    # )
    # def test_no_change(self, tmpdir, code):
    #     self.run_and_assert(tmpdir, code, code)
    #
