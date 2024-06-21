import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.lazy_logging import LazyLogging

logging_funcs = {"debug", "info", "warning", "warn", "error", "critical"}
each_func = pytest.mark.parametrize("func", sorted(logging_funcs))


class TestLazyLoggingModulo(BaseCodemodTest):
    codemod = LazyLogging

    def test_name(self):
        assert self.codemod.name == "lazy-logging"

    @each_func
    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                import logging
                e = "error"
                logging.{}("Error occurred: %s" % e)
                """,
                """
                import logging
                e = "error"
                logging.{}("Error occurred: %s", e)
                """,
            ),
            (
                """
                import logging
                logging.{}("Error occurred: %s" % ("one",))
                """,
                """
                import logging
                logging.{}("Error occurred: %s", "one")
                """,
            ),
            (
                """
                import logging
                log = logging.getLogger('anything')
                log.{}("one: %s, two: %s" % ("one", "two"))
                """,
                """
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
                """
                import logging
                e = "error"
                logging.log(logging.ERROR, "Error occurred: %s" % e)
                """,
                """
                import logging
                e = "error"
                logging.log(logging.ERROR, "Error occurred: %s", e)
                """,
            ),
            (
                """
                import logging
                logging.log(logging.ERROR, "Error occurred: %s" % ("one",))
                """,
                """
                import logging
                logging.log(logging.ERROR, "Error occurred: %s", "one")
                """,
            ),
            (
                """
                import logging
                log = logging.getLogger('anything')
                log.log(logging.INFO, "one: %s, two: %s" % ("one", "two"))
                """,
                """
                import logging
                log = logging.getLogger('anything')
                log.log(logging.INFO, "one: %s, two: %s", "one", "two")
                """,
            ),
            (
                """
                from logging import log, INFO
                e = "error"
                log(INFO, "Error occurred: %s" % e)
                """,
                """
                from logging import log, INFO
                e = "error"
                log(INFO, "Error occurred: %s", e)
                """,
            ),
            (
                """
                from logging import getLogger, ERROR
                getLogger('anything').log(ERROR, "one: %s, two: %s" % ("one", "two"))
                """,
                """
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
                """
                from logging import {0}
                e = "error"
                {0}("Error occurred: %s" % e)
                """,
                """
                from logging import {0}
                e = "error"
                {0}("Error occurred: %s", e)
                """,
            ),
            (
                """
                from logging import getLogger
                getLogger('anything').{}("one: %s, two: %s" % ("one", "two"))
                """,
                """
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
                """
                from logging import {} as log_func
                e = "error"
                log_func("Error occurred: %s" % e)
                """,
                """
                from logging import {} as log_func
                e = "error"
                log_func("Error occurred: %s", e)
                """,
            ),
            (
                """
                from logging import getLogger as make_logger
                make_logger('anything').{}("one: %s, two: %s" % ("one", "two"))
                """,
                """
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
        input_code = """
        import logging
        log = logging.getLogger('foo')
        def some_function(logger):
            logger.debug("hi: %s" % 'hello')
        some_function(log)
        """
        expected_code = """
        import logging
        log = logging.getLogger('foo')
        def some_function(logger):
            logger.debug("hi: %s", 'hello')
        some_function(log)
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    def test_log_format_specifiers(self, tmpdir):
        input_code = """
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
        expected_code = """
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
        input_code = """
        import logging
        logging.info("Name: %s" % "Alice", exc_info=True, extra={'custom_info': 'extra details'}, stacklevel=2)
        """
        expected_code = """
        import logging
        logging.info("Name: %s", "Alice", exc_info=True, extra={'custom_info': 'extra details'}, stacklevel=2)
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                import logging
                var = b"three"
                logging.info(b"one %s" % var)
                """,
                """
                import logging
                var = b"three"
                logging.info(b"one %s", var)
                """,
            ),
            (
                """
                import logging
                four = r" four"
                logging.info(r"two \\n%s" %  four)
                """,
                """
                import logging
                four = r" four"
                logging.info(r"two \\n%s", four)
                """,
            ),
        ],
    )
    def test_log_prefix_types(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_var_assignments(self, tmpdir):
        input_code = """
        import logging
        msg = "something %s"
        e = "error"
        logging.info(msg % e)
        """
        expected_code = """
        import logging
        msg = "something %s"
        e = "error"
        logging.info(msg, e)
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    @pytest.mark.parametrize(
        "code",
        [
            """
            import logging
            logging.info("something")
            """,
            """
            import logging
            logging.info("% something", "hi")
            """,
            """
            import logging
            logging.info("% something", "hi")
            """,
            """
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(
                "At depth %d, updating best step: %s (score: %f).",
                10,
                [swap] + next_step.swaps_added,
                next_score,
            )
            """,
            """
            import logging
            logger = logging.getLogger(__name__)
            logger.log(
                logging.INFO,
                "At depth %d, updating best step: %s (score: %f).",
                10,
                [swap] + next_step.swaps_added,
                next_score,
            )
            """,
        ],
    )
    def test_no_change(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)


class TestLazyLoggingPlus(BaseCodemodTest):
    codemod = LazyLogging

    @each_func
    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                import logging
                e = "error"
                logging.{}("Error occurred: " + e)
                """,
                """
                import logging
                e = "error"
                logging.{}("Error occurred: %s", e)
                """,
            ),
            (
                """
                import logging
                num = 2
                logging.{}("Num:" + str(num))
                """,
                """
                import logging
                num = 2
                logging.{}("Num:%s", str(num))
                """,
            ),
            (
                """
                import logging
                log = logging.getLogger('anything')
                one = "1"
                log.{}("one " + one + " two " + "2")
                """,
                """
                import logging
                log = logging.getLogger('anything')
                one = "1"
                log.{}("one %s two 2", one)
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
                """
                import logging
                e = "error"
                logging.log(logging.ERROR, "Error occurred: " + e)
                """,
                """
                import logging
                e = "error"
                logging.log(logging.ERROR, "Error occurred: %s", e)
                """,
            ),
            (
                """
                import logging
                log = logging.getLogger('anything')
                one = "1"
                log.log(logging.INFO, "one " + one + " two " + "2")
                """,
                """
                import logging
                log = logging.getLogger('anything')
                one = "1"
                log.log(logging.INFO, "one %s two 2", one)
                """,
            ),
            (
                """
                from logging import log, INFO
                e = "error"
                log(INFO, "Error occurred: " + e)
                """,
                """
                from logging import log, INFO
                e = "error"
                log(INFO, "Error occurred: %s", e)
                """,
            ),
            (
                """
                from logging import getLogger, ERROR
                one = "1"
                getLogger('anything').log(ERROR, "one " + one + " two " + "2")
                """,
                """
                from logging import getLogger, ERROR
                one = "1"
                getLogger('anything').log(ERROR, "one %s two 2", one)
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
                """
                from logging import {0}
                e = "error"
                {0}("Error occurred: " + e)
                """,
                """
                from logging import {0}
                e = "error"
                {0}("Error occurred: %s", e)
                """,
            ),
            (
                """
                from logging import getLogger
                one = "1"
                getLogger('anything').{}("one " + one + " two" + "2")
                """,
                """
                from logging import getLogger
                one = "1"
                getLogger('anything').{}("one %s two2", one)
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
                """
                from logging import {} as log_func
                e = "error"
                log_func("Error occurred: " + e)
                """,
                """
                from logging import {} as log_func
                e = "error"
                log_func("Error occurred: %s", e)
                """,
            ),
            (
                """
                from logging import getLogger as make_logger
                one = "1"
                make_logger('anything').{}("one " + one + " two " + "2")
                """,
                """
                from logging import getLogger as make_logger
                one = "1"
                make_logger('anything').{}("one %s two 2", one)
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
        input_code = """
        import logging
        log = logging.getLogger('foo')
        def some_function(logger):
            logger.debug("hi: " + 'hello')
        some_function(log)
        """
        expected_code = """
        import logging
        log = logging.getLogger('foo')
        def some_function(logger):
            logger.debug("hi: %s", 'hello')
        some_function(log)
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    @pytest.mark.xfail(reason="Not currently supported")
    def test_log_format_specifiers(self, tmpdir):
        input_code = """
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
        expected_code = """
        import logging
        name = "Alice"
        age = 30
        height = 1.68
        balance = 12345.67
        hex_id = 255
        octal_num = 8
        scientific_val = 1234.56789
        logging.info("User Info - Name: %s, Age: %s, Height: %s, Balance: %s, ID (hex): %s, Number (octal): %s, Scientific Value: %s", name, str(age), str(round(height, 2)), str(round(balance, 2)), format(hex_id, 'x'), format(octal_num, 'o'), format(scientific_val, '.2e'))
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    def test_log_kwargs(self, tmpdir):
        input_code = """
        import logging
        name = "alice"
        logging.info("Name: " + name, exc_info=True, extra={'custom_info': 'extra details'}, stacklevel=2)
        """
        expected_code = """
        import logging
        name = "alice"
        logging.info("Name: %s", name, exc_info=True, extra={'custom_info': 'extra details'}, stacklevel=2)
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                import logging
                var = b"three"
                logging.info(b"one " + var)
                """,
                """
                import logging
                var = b"three"
                logging.info(b"one %s", var)
                """,
            ),
            (
                """
                import logging
                var = "three"
                logging.info("one " + "two " + var)
                """,
                """
                import logging
                var = "three"
                logging.info("one two %s", var)
                """,
            ),
            (
                """
                import logging
                four = r" four"
                logging.info(r"two \\n" +  four)
                """,
                """
                import logging
                four = r" four"
                logging.info(r"two \\n%s", four)
                """,
            ),
            (
                """
                import logging
                var = r"three"
                logging.info(r"one " + r"two " + var)
                """,
                """
                import logging
                var = r"three"
                logging.info(r"one two %s", var)
                """,
            ),
        ],
    )
    def test_log_prefix_types(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.xfail(reason="Not currently supported")
    def test_log_mixed_prefixes(self, tmpdir):
        input_code = """
        import logging
        four = u" four"
        logging.info("one: " + r"two \\n" + u'three '+  four)
        """
        expected_code = """
        import logging
        four = u" four"
        logging.info("one: " + r"two \\n" + u'three %s' , four)
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    @pytest.mark.parametrize(
        "code",
        [
            """
            import logging
            logging.info("one" + "two")
            """,
            """
            import logging
            logging.info("%s" + "hi")
            """,
            """
            import logging
            logging.info("one" + "%s" + "three %s")
            """,
            """
            import logging
            logging.info(2+2)
            """,
            """
            import logging
            var = 2
            logging.info(var + var)
            """,
            """
            import logging
            msg = "one"
            var = "two"
            res = msg + var
            logging.info(res)
            """,
            # User intention is unclear here, did they
            # Want a `%s` literal or no?
            """
            import logging
            var = "something"
            logging.info("Something occurred: %s " + var)
            """,
            # There are more `%` operators than there are variables so
            # We will not attempt to change the code.
            """
            import logging
            e = "error"
            logging.error("Error %s occurred: %s " + e)
            """,
        ],
    )
    def test_no_change(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)

    @pytest.mark.xfail(reason="Not currently supported")
    def test_modulo_and_plus(self, tmpdir):
        input_code = """
        import logging
        var = "three"
        logging.info("one %s" % 'two ' + var + ' four')
        """
        expected_code = """
        import logging
        var = "three"
        logging.info("one %s %s four", 'two', var)
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                import logging
                e = "error"
                msg = "something %s"
                logging.info(msg + e)
                """,
                """
                import logging
                e = "error"
                msg = "something %s"
                logging.info("%s%s", msg, e)
                """,
            ),
            (
                """
                import logging
                one = "one"
                two = "two"
                logging.info(one + two)
                """,
                """
                import logging
                one = "one"
                two = "two"
                logging.info("%s%s", one, two)
                """,
            ),
        ],
    )
    def test_var_assignments_with_modulo(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)
