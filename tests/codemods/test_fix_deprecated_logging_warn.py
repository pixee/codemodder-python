import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.fix_deprecated_logging_warn import FixDeprecatedLoggingWarn


class TestFixDeprecatedLoggingWarn(BaseCodemodTest):
    codemod = FixDeprecatedLoggingWarn

    @pytest.mark.parametrize(
        "code",
        [
            """
        import logging
        logging.{}('something')
        """,
            """
        import logging
        logging.{}("something %s and %s", "foo", "bar")
        """,
            """
        import logging
        log = logging.getLogger('anything')
        log.{}('something')
        """,
        ],
    )
    def test_import(self, tmpdir, code):
        original_code = code.format("warn")
        new_code = code.format("warning")
        self.run_and_assert(tmpdir, original_code, new_code)

    @pytest.mark.parametrize(
        "code",
        [
            """
        from logging import {0}
        {0}('something')
        """,
            """
        from logging import getLogger
        getLogger('anything').{0}('something')
        """,
        ],
    )
    def test_from_import(self, tmpdir, code):
        original_code = code.format("warn")
        new_code = code.format("warning")
        self.run_and_assert(tmpdir, original_code, new_code)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                from logging import warn as warn_func
                warn_func('something')""",
                """
                from logging import warning
                warning('something')""",
            ),
            (
                """
                from logging import getLogger as make_logger
                logger = make_logger('anything')
                logger.warn('something')""",
                """
                from logging import getLogger as make_logger
                logger = make_logger('anything')
                logger.warning('something')""",
            ),
        ],
    )
    def test_import_alias(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize(
        "code",
        [
            """
        import xyz
        xyz.warn('something')
        """,
            """
        import my_logging
        log = my_logging.getLogger('anything')
        log.warn('something')
        """,
        ],
    )
    def test_different_warn(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)

    @pytest.mark.xfail(reason="Not currently supported")
    def test_log_as_arg(self, tmpdir):
        code = """
        import logging
        log = logging.getLogger('foo')
        def some_function(logger):
            logger.{}("hi")
        some_function(log)
        """
        original_code = code.format("warn")
        new_code = code.format("warning")
        self.run_and_assert(tmpdir, original_code, new_code)
