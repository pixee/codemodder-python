import pytest
from core_codemods.fix_empty_sequence_comparison import FixEmptySequenceComparison
from tests.codemods.base_codemod_test import BaseCodemodTest


class TestFixEmptySequenceComparison(BaseCodemodTest):
    codemod = FixEmptySequenceComparison

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
            x = [1]
            if x != []:
                pass
            """,
                """
            x = [1]
            if x:
                pass
            """,
            ),
            (
                """
            x = [1]
            if [] != x:
                pass
            """,
                """
            x = [1]
            if x:
                pass
            """,
            ),
            (
                """
            x = [1]
            if x == []:
                pass
            """,
                """
            x = [1]
            if not x:
                pass
            """,
            ),
            (
                """
            x = [1]
            if [] == x:
                pass
            """,
                """
            x = [1]
            if not x:
                pass
            """,
            ),
            (
                """
            if [1, 2] == []:
                pass
            """,
                """
            if not [1, 2]:
                pass
            """,
            ),
        ],
    )
    def test_change_list_if_statements(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)
        assert len(self.file_context.codemod_changes) == 1

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
            x = {1: "one", 2: "two"}
            if x != {}:
                pass
            """,
                """
            x = {1: "one", 2: "two"}
            if x:
                pass
            """,
            ),
            (
                """
            x = {1: "one", 2: "two"}
            if {} != x:
                pass
            """,
                """
            x = {1: "one", 2: "two"}
            if x:
                pass
            """,
            ),
            (
                """
            x = {1: "one", 2: "two"}
            if x == {}:
                pass
            """,
                """
            x = {1: "one", 2: "two"}
            if not x:
                pass
            """,
            ),
            (
                """
            x = {1: "one", 2: "two"}
            if {} == x:
                pass
            """,
                """
            x = {1: "one", 2: "two"}
            if not x:
                pass
            """,
            ),
            (
                """
            if {1: "one", 2: "two"} == {}:
                pass
            """,
                """
            if not {1: "one", 2: "two"}:
                pass
            """,
            ),
        ],
    )
    def test_change_dict_if_statements(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)
        assert len(self.file_context.codemod_changes) == 1

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
            x = (1, 2, 3)
            if x != ():
                pass
            """,
                """
            x = (1, 2, 3)
            if x:
                pass
            """,
            ),
            (
                """
            x = (1, 2, 3)
            if () != x:
                pass
            """,
                """
            x = (1, 2, 3)
            if x:
                pass
            """,
            ),
            (
                """
            x = (1, 2, 3)
            if x == ():
                pass
            """,
                """
            x = (1, 2, 3)
            if not x:
                pass
            """,
            ),
            (
                """
            x = (1, 2, 3)
            if () == x:
                pass
            """,
                """
            x = (1, 2, 3)
            if not x:
                pass
            """,
            ),
            (
                """
            if (1, 2, 3) == ():
                pass
            """,
                """
            if not (1, 2, 3):
                pass
            """,
            ),
        ],
    )
    def test_change_tuple_if_statements(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)
        assert len(self.file_context.codemod_changes) == 1


# no change
# if x == 'hi', x is [],
# @pytest.mark.parametrize(
#     "code",
#     [
#         """
#     from logging import {0}
#     {0}('something')
#     """,
#         """
#     from logging import getLogger
#     getLogger('anything').{0}('something')
#     """,
#     ],
# )
# def test_from_import(self, tmpdir, code):
#     original_code = code.format("warn")
#     new_code = code.format("warning")
#     self.run_and_assert(tmpdir, original_code, new_code)
#     assert len(self.file_context.codemod_changes) == 1
#
# @pytest.mark.parametrize(
#     "input_code,expected_output",
#     [
#         (
#             """\
#             from logging import warn as warn_func
#             warn_func('something')""",
#             """\
#             from logging import warning
#             warning('something')""",
#         ),
#         (
#             """\
#             from logging import getLogger as make_logger
#             logger = make_logger('anything')
#             logger.warn('something')""",
#             """\
#             from logging import getLogger as make_logger
#             logger = make_logger('anything')
#             logger.warning('something')""",
#         ),
#     ],
# )
# def test_import_alias(self, tmpdir, input_code, expected_output):
#     self.run_and_assert(tmpdir, input_code, expected_output)
#     assert len(self.file_context.codemod_changes) == 1
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
#     assert len(self.file_context.codemod_changes) == 0
#
# @pytest.mark.xfail(reason="Not currently supported")
# def test_log_as_arg(self, tmpdir):
#     code = """\
#     import logging
#     log = logging.getLogger('foo')
#     def some_function(logger):
#         logger.()("hi")
#     some_function(log)
#     """
#     original_code = code.format("warn")
#     new_code = code.format("warning")
#     self.run_and_assert(tmpdir, original_code, new_code)
#     assert len(self.file_context.codemod_changes) == 1
