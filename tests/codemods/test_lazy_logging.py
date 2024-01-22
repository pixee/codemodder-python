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

    @pytest.mark.xfail(reason="Not currently supported")
    def test_log_as_arg(self, tmpdir):
        input_code = """\
        import logging
        log = logging.getLogger('foo')
        def some_function(logger):
            logger.debug("hi: %s" % 'hello')
        some_function(log)
        """
        expected_code = """\
        import logging
        log = logging.getLogger('foo')
        def some_function(logger):
            logger.debug("hi: %s", 'hello')
        some_function(log)
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    def test_log_format_specifiers(self, tmpdir):
        input_code = """\
        import logging
        name = "Alice"
        age = 30
        height = 1.68
        balance = 12345.67
        hex_id = 255
        octal_num = 8
        scientific_val = 1234.56789
        logging.info("User Info - Name: %s, Age: %d, Height: %.2f, Balance: %.2f, ID (hex): %x, Number (octal): %o, Scientific Value: %.2e" % (name, age, height, balance, hex_id, octal_num, scientific_val))
        """
        expected_code = """\
        import logging
        name = "Alice"
        age = 30
        height = 1.68
        balance = 12345.67
        hex_id = 255
        octal_num = 8
        scientific_val = 1234.56789
        logging.info("User Info - Name: %s, Age: %d, Height: %.2f, Balance: %.2f, ID (hex): %x, Number (octal): %o, Scientific Value: %.2e", name, age, height, balance, hex_id, octal_num, scientific_val)
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    def test_log_kwargs(self, tmpdir):
        input_code = """\
        import logging
        logging.info("Name: %s" % "Alice", exc_info=True, extra={'custom_info': 'extra details'}, stacklevel=2)
        """
        expected_code = """\
        import logging
        logging.info("Name: %s", "Alice", exc_info=True, extra={'custom_info': 'extra details'}, stacklevel=2)
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    @pytest.mark.parametrize(
        "code",
        [
            """\
            import logging
            logging.info("something")
            """,
            """\
            import logging
            logging.info("% something", "hi")
            """,
            """\
            import logging
            logging.info("% something", "hi")
            """,
            """\
            import logging
            var = "3"
            logging.info("var %s" + var)
            """,
        ],
    )
    def test_no_change(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)
