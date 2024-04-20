import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.combine_isinstance_issubclass import CombineIsinstanceIssubclass

each_func = pytest.mark.parametrize("func", ["isinstance", "issubclass"])


class TestCombineIsinstanceIssubclass(BaseCodemodTest):
    codemod = CombineIsinstanceIssubclass

    def test_name(self):
        assert self.codemod.name == "combine-isinstance-issubclass"

    @each_func
    def test_combine(self, tmpdir, func):
        input_code = f"""
        {func}(x, str) or {func}(x, bytes)
        """
        expected = f"""
        {func}(x, (str, bytes))
        """
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize(
        "code",
        [
            "isinstance(x, str)",
            "isinstance(x, (str, bytes))",
            "isinstance(x, str) and isinstance(x, bytes)",
            "isinstance(x, str) and isinstance(x, str) or True",
            "isinstance(x, str) or issubclass(x, str)",
            "isinstance(x, str) or isinstance(y, str)",
        ],
    )
    def test_no_change(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        x = "foo"
        isinstance(x, str) or isinstance(x, bytes)
        """
        lines_to_exclude = [3]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )

    def _format_func_run_test(self, tmpdir, func, input_code, expected, num_changes=1):
        self.run_and_assert(
            tmpdir,
            input_code.replace("{func}", func),
            expected.replace("{func}", func),
            num_changes,
        )

    @each_func
    @pytest.mark.parametrize(
        "input_code, expected",
        [
            # Tuple on the left
            (
                "{func}(x, (str, bytes)) or {func}(x, bytearray)",
                "{func}(x, (str, bytes, bytearray))",
            ),
            # Tuple on the right
            (
                "{func}(x, str) or {func}(x, (bytes, bytearray))",
                "{func}(x, (str, bytes, bytearray))",
            ),
            # Tuple on both sides no duplicates
            (
                "{func}(x, (str, bytes)) or {func}(x, (bytearray, memoryview))",
                "{func}(x, (str, bytes, bytearray, memoryview))",
            ),
            # Tuple on both sides with duplicates
            (
                "{func}(x, (str, bytes)) or {func}(x, (str, bytes, bytearray))",
                "{func}(x, (str, bytes, bytearray))",
            ),
        ],
    )
    def test_combine_tuples(self, tmpdir, func, input_code, expected):
        self._format_func_run_test(tmpdir, func, input_code, expected)

    @each_func
    @pytest.mark.parametrize(
        "input_code, expected",
        [
            # 3 cst.Names
            (
                "{func}(x, str) or {func}(x, bytes) or {func}(x, bytearray)",
                "{func}(x, (str, bytes, bytearray))",
            ),
            # 4 cst.Names
            (
                "{func}(x, str) or {func}(x, bytes) or {func}(x, bytearray) or {func}(x, some_type)",
                "{func}(x, (str, bytes, bytearray, some_type))",
            ),
            # 5 cst.Names
            (
                "{func}(x, str) or {func}(x, bytes) or {func}(x, bytearray) or {func}(x, some_type) or {func}(x, another_type)",
                "{func}(x, (str, bytes, bytearray, some_type, another_type))",
            ),
            # 2 cst.Names and 1 cst.Tuple
            (
                "{func}(x, str) or {func}(x, bytes) or {func}(x, (bytearray, memoryview))",
                "{func}(x, (str, bytes, bytearray, memoryview))",
            ),
            # 2 cst.Name and 2 cst.Tuples
            (
                "{func}(x, str) or {func}(x, (bytes, bytearray)) or {func}(x, (memoryview, bytearray)) or {func}(x, list)",
                "{func}(x, (str, bytes, bytearray, memoryview, list))",
            ),
            # 3 cst.Tuples
            (
                "{func}(x, (str, bytes)) or {func}(x, (bytes, bytearray)) or {func}(x, (bytearray, memoryview))",
                "{func}(x, (str, bytes, bytearray, memoryview))",
            ),
            # 4 cst.Tuples
            (
                "{func}(x, (str, bytes)) or {func}(x, (bytes, bytearray)) or {func}(x, (bytearray, memoryview)) or {func}(x, (memoryview, str))",
                "{func}(x, (str, bytes, bytearray, memoryview))",
            ),
        ],
    )
    def test_more_than_two_calls(self, tmpdir, func, input_code, expected):
        self._format_func_run_test(
            tmpdir, func, input_code, expected, input_code.count(" or ")
        )
