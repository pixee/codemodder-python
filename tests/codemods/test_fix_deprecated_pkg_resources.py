import pytest

from codemodder.codemods.test import BaseSemgrepCodemodTest
from core_codemods.fix_deprecated_pkg_resources import FixDeprecatedPkgResources


class TestFixDeprecatedPkgResources(BaseSemgrepCodemodTest):
    codemod = FixDeprecatedPkgResources

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                import pkg_resources
                dist = pkg_resources.get_distribution("package_name")
                """,
                """
                from importlib.metadata import distribution

                dist = distribution("package_name")
                """,
            ),
            (
                """
                import pkg_resources
                version = pkg_resources.get_distribution("package_name").version
                """,
                """
                from importlib.metadata import distribution

                version = distribution("package_name").version
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
                from pkg_resources import get_distribution
                dist = get_distribution("package_name")
                """,
                """
                from importlib.metadata import distribution

                dist = distribution("package_name")
                """,
            ),
            (
                """
                from pkg_resources import get_distribution
                version = get_distribution("package_name").version
                """,
                """
                from importlib.metadata import distribution

                version = distribution("package_name").version
                """,
            ),
        ],
    )
    def test_from_import(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    #
    # @pytest.mark.parametrize(
    #     "input_code,expected_output",
    #     [
    #         (
    #             """
    #             from logging import warn as warn_func
    #             warn_func('something')""",
    #             """
    #             from logging import warning
    #             warning('something')""",
    #         ),
    #         (
    #             """
    #             from logging import getLogger as make_logger
    #             logger = make_logger('anything')
    #             logger.warn('something')""",
    #             """
    #             from logging import getLogger as make_logger
    #             logger = make_logger('anything')
    #             logger.warning('something')""",
    #         ),
    #     ],
    # )
    # def test_import_alias(self, tmpdir, input_code, expected_output):
    #     self.run_and_assert(tmpdir, input_code, expected_output)
    #
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
