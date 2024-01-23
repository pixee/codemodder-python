import pytest
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest
from core_codemods.lazy_logging import LazyLogging

logging_funcs = {"debug", "info", "warning", "error", "critical"}
each_func = pytest.mark.parametrize("func", logging_funcs)


class TestLazyLoggingModulo(BaseSemgrepCodemodTest):
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

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """\
            import logging
            e = "error"
            logging.log(logging.ERROR, "Error occurred: %s" % e)
            """,
                """\
            import logging
            e = "error"
            logging.log(logging.ERROR, "Error occurred: %s", e)
            """,
            ),
            (
                """\
            import logging
            logging.log(logging.ERROR, "Error occurred: %s" % ("one",))
            """,
                """\
            import logging
            logging.log(logging.ERROR, "Error occurred: %s", "one")
            """,
            ),
            (
                """\
            import logging
            log = logging.getLogger('anything')
            log.log(logging.INFO, "one: %s, two: %s" % ("one", "two"))
            """,
                """\
            import logging
            log = logging.getLogger('anything')
            log.log(logging.INFO, "one: %s, two: %s", "one", "two")
            """,
            ),
            (
                """\
            from logging import log, INFO
            e = "error"
            log(INFO, "Error occurred: %s" % e)
            """,
                """\
            from logging import log, INFO
            e = "error"
            log(INFO, "Error occurred: %s", e)
            """,
            ),
            (
                """\
            from logging import getLogger, ERROR
            getLogger('anything').log(ERROR, "one: %s, two: %s" % ("one", "two"))
            """,
                """\
            from logging import getLogger, ERROR
            getLogger('anything').log(ERROR, "one: %s, two: %s", "one", "two")
            """,
            ),
        ],
    )
    def test_log_func(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

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
        xyz.info("hi: %s" % 'hello')
        """,
            """
        import my_logging
        log = my_logging.getLogger('anything')
        log.info("hi: %s" % 'hello')
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
        ],
    )
    def test_no_change(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)


@pytest.mark.skip("Need to add support")
class TestLazyLoggingPlus(BaseSemgrepCodemodTest):
    codemod = LazyLogging

    @each_func
    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """\
            import logging
            e = "error"
            logging.{}("Error occurred: " + e)
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
            e = "error"
            logging.{}("Error occurred: %s" + e)
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
            log = logging.getLogger('anything')
            one = "1"
            log.{}("one " + one + " two " + "2")
            """,
                """\
            import logging
            log = logging.getLogger('anything')
            one = "1"
            log.{}("one %s two %s", one, "2")
            """,
            ),
        ],
    )
    def test_import(self, tmpdir, input_code, expected_output, func):
        self.run_and_assert(
            tmpdir, input_code.format(func), expected_output.format(func)
        )

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """\
            import logging
            e = "error"
            logging.log(logging.ERROR, "Error occurred: " + e)
            """,
                """\
            import logging
            e = "error"
            logging.log(logging.ERROR, "Error occurred: %s", e)
            """,
            ),
            (
                """\
            import logging
            log = logging.getLogger('anything')
            one = "1"
            log.log(logging.INFO, "one %s" + one + " two " + "2")
            """,
                """\
            import logging
            log = logging.getLogger('anything')
            one = "1"
            log.log(logging.INFO, "one %s two %s", one, "2")
            """,
            ),
            (
                """\
            from logging import log, INFO
            e = "error"
            log(INFO, "Error occurred: " + e)
            """,
                """\
            from logging import log, INFO
            e = "error"
            log(INFO, "Error occurred: %s", e)
            """,
            ),
            (
                """\
            from logging import getLogger, ERROR
            one = "1"
            getLogger('anything').log(ERROR, "one " + one + " two " + "2")
            """,
                """\
            from logging import getLogger, ERROR
            one = "1"
            getLogger('anything').log(ERROR, "one %s two %s", one, "2")
            """,
            ),
        ],
    )
    def test_log_func(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    @each_func
    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """\
            from logging import {0}
            e = "error"
            {0}("Error occurred: " + e)
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
            one = "1"
            getLogger('anything').{}("one " + one + " two %s" + "2")
            """,
                """\
            from logging import getLogger
            one = "1"
            getLogger('anything').{}("one %s two %s", one, "2")
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
            log_func("Error occurred: " + e)
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
            one = "1"
            make_logger('anything').{}("one " + one + " two " + "2")
            """,
                """\
            from logging import getLogger as make_logger
            one = "1"
            make_logger('anything').{}("one %s two %s", one, "2")
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
        var = "hello"
        xyz.info("hi: + var)
        """,
            """
        import my_logging
        log = my_logging.getLogger('anything')
        var = "hello"
        log.info("hi:" + var)
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
            logger.debug("hi: " + 'hello')
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
        logging.info("User Info - Name: " + name + 
             ", Age: " + str(age) + 
             ", Height: " + str(round(height, 2)) + 
             ", Balance: " + str(round(balance, 2)) + 
             ", ID (hex): " + format(hex_id, 'x') + 
             ", Number (octal): " + format(octal_num, 'o') + 
             ", Scientific Value: " + format(scientific_val, '.2e'))
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
        name = "alice"
        logging.info("Name: " + name, exc_info=True, extra={'custom_info': 'extra details'}, stacklevel=2)
        """
        expected_code = """\
        import logging
        name = "alice"
        logging.info("Name: %s", name, exc_info=True, extra={'custom_info': 'extra details'}, stacklevel=2)
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    @pytest.mark.parametrize(
        "code",
        [
            """\
            import logging
            logging.info("one" + "two")
            """,
            """\
            import logging
            logging.info("%s" + "hi")
            """,
            """\
            import logging
            logging.info("one" + "%s" + "three %s")
            """,
        ],
    )
    def test_no_change(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)