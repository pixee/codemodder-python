from codemodder.codemods.test import BaseCodemodTest
from core_codemods.timezone_aware_datetime import TimezoneAwareDatetime


class TestTimezoneAwareDatetimeNeedKwarg(BaseCodemodTest):
    codemod = TimezoneAwareDatetime

    def test_name(self):
        assert self.codemod.name == "timezone-aware-datetime"

    def test_no_change(self, tmpdir):
        input_code = """
        import datetime
        from zoneinfo import ZoneInfo  
        
        eastern =  ZoneInfo("America/New_York")
        datetime.datetime(2021, 12, 25, 15, 30, 0, tzinfo=eastern)
        
        datetime.datetime.now(ZoneInfo("America/New_York"))
        datetime.datetime.now(tz=eastern)
        
        datetime.datetime.fromtimestamp(time.time(), eastern)
        datetime.datetime.fromtimestamp(time.time(), tz=eastern)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_import_datetime(self, tmpdir):
        input_code = """
        import datetime
        import time
        datetime.datetime(2021, 12, 25, 15, 30, 0)
        
        datetime.datetime.now()
        
        datetime.datetime.fromtimestamp(time.time())
        """
        expected = """
        import datetime
        import time
        datetime.datetime(2021, 12, 25, 15, 30, 0, tzinfo=datetime.timezone.utc)
        
        datetime.datetime.now(tz=datetime.timezone.utc)

        datetime.datetime.fromtimestamp(time.time(), tz=datetime.timezone.utc)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=3)

    # import from, import alias

    # @pytest.mark.parametrize(
    #     "code",
    #     [
    #         "x.startswith('foo')",
    #         "x.startswith(('f', 'foo'))",
    #         "x.startswith('foo') and x.startswith('f')",
    #         "x.startswith('foo') and x.startswith('f') or True",
    #         "x.startswith('foo') or x.endswith('f')",
    #         "x.startswith('foo') or y.startswith('f')",
    #         "x.startswith('foo') or y.startswith('f') or x.startswith('f')",
    #     ],
    # )
    # def test_no_change(self, tmpdir, code):
    #     self.run_and_assert(tmpdir, code, code)
    #
    # def test_exclude_line(self, tmpdir):
    #     input_code = (
    #         expected
    #     ) = """
    #     x = "foo"
    #     x.startswith("foo") or x.startswith("f")
    #     """
    #     lines_to_exclude = [3]
    #     self.run_and_assert(
    #         tmpdir,
    #         input_code,
    #         expected,
    #         lines_to_exclude=lines_to_exclude,
    #     )
    #
    # def _format_func_run_test(self, tmpdir, func, input_code, expected, num_changes=1):
    #     self.run_and_assert(
    #         tmpdir,
    #         input_code.replace("{func}", func),
    #         expected.replace("{func}", func),
    #         num_changes,
    #     )
    #
    # @each_func
    # @pytest.mark.parametrize(
    #     "input_code, expected",
    #     [
    #         # Tuple on the left
    #         (
    #             "x.{func}(('f', 'foo')) or x.{func}('bar')",
    #             "x.{func}(('f', 'foo', 'bar'))",
    #         ),
    #         # Tuple on the right
    #         (
    #             "x.{func}('f') or x.{func}(('foo', 'bar'))",
    #             "x.{func}(('f', 'foo', 'bar'))",
    #         ),
    #         # Tuple on both sides
    #         (
    #             "x.{func}(('1', '2')) or x.{func}(('3', '4'))",
    #             "x.{func}(('1', '2', '3', '4'))",
    #         ),
    #         # Tuples on both sides with duplicate elements
    #         (
    #             "x.{func}(('1', '2', '3')) or x.{func}(('2', '3', '4'))",
    #             "x.{func}(('1', '2', '3', '4'))",
    #         ),
    #     ],
    # )
    # def test_combine_tuples(self, tmpdir, func, input_code, expected):
    #     self._format_func_run_test(tmpdir, func, input_code, expected)
    #
    # @each_func
    # @pytest.mark.parametrize(
    #     "input_code, expected",
    #     [
    #         # cst.ConcatenatedString on the left
    #         (
    #             "x.{func}('foo' 'bar') or x.{func}('baz')",
    #             "x.{func}(('foo' 'bar', 'baz'))",
    #         ),
    #         # cst.ConcatenatedString on the right
    #         (
    #             "x.{func}('foo') or x.{func}('bar' 'baz')",
    #             "x.{func}(('foo', 'bar' 'baz'))",
    #         ),
    #         # cst.ConcatenatedString on both sides
    #         (
    #             "x.{func}('foo' 'bar') or x.{func}('baz' 'qux')",
    #             "x.{func}(('foo' 'bar', 'baz' 'qux'))",
    #         ),
    #     ],
    # )
    # def test_concat_string_args(self, tmpdir, func, input_code, expected):
    #     self._format_func_run_test(tmpdir, func, input_code, expected)
    #
    # @each_func
    # @pytest.mark.parametrize(
    #     "input_code, expected",
    #     [
    #         # cst.FormattedString on the left
    #         (
    #             "x.{func}(f'formatted {foo}') or x.{func}('bar')",
    #             "x.{func}((f'formatted {foo}', 'bar'))",
    #         ),
    #         # cst.FormattedString on the right
    #         (
    #             "x.{func}('foo') or x.{func}(f'formatted {bar}')",
    #             "x.{func}(('foo', f'formatted {bar}'))",
    #         ),
    #         # cst.FormattedString on both sides
    #         (
    #             "x.{func}(f'formatted {foo}') or x.{func}(f'formatted {bar}')",
    #             "x.{func}((f'formatted {foo}', f'formatted {bar}'))",
    #         ),
    #     ],
    # )
    # def test_format_string_args(self, tmpdir, func, input_code, expected):
    #     self._format_func_run_test(tmpdir, func, input_code, expected)
    #
    # @each_func
    # @pytest.mark.parametrize(
    #     "input_code, expected",
    #     [
    #         # cst.Name on the left
    #         ("x.{func}(y) or x.{func}('foo')", "x.{func}((y, 'foo'))"),
    #         # cst.Name on the right
    #         ("x.{func}('foo') or x.{func}(y)", "x.{func}(('foo', y))"),
    #         # cst.Name on both sides
    #         ("x.{func}(y) or x.{func}(z)", "x.{func}((y, z))"),
    #         # cst.Name in tuple on the left
    #         ("x.{func}((y, 'foo')) or x.{func}('bar')", "x.{func}((y, 'foo', 'bar'))"),
    #         # cst.Name in tuple on the right
    #         ("x.{func}('foo') or x.{func}((y, 'bar'))", "x.{func}(('foo', y, 'bar'))"),
    #         # cst.Name in tuple on both sides
    #         (
    #             "x.{func}((y, 'foo')) or x.{func}((z, 'bar'))",
    #             "x.{func}((y, 'foo', z, 'bar'))",
    #         ),
    #     ],
    # )
    # def test_name_args(self, tmpdir, func, input_code, expected):
    #     self._format_func_run_test(tmpdir, func, input_code, expected)
    #
    # _10_of_each_type = [
    #     (f"'{i}'", f"'{i}con' 'cat{i}'", f"f'fmt{i}'", f"name{i}") for i in range(10)
    # ]
    #
    # @each_func
    # @pytest.mark.parametrize(
    #     "input_code, expected",
    #     [
    #         # 3 cst.SimpleStrings
    #         (
    #             "x.{func}('foo') or x.{func}('bar') or x.{func}('baz')",
    #             "x.{func}(('foo', 'bar', 'baz'))",
    #         ),
    #         # 3 cst.SimpleStrings with duplicates
    #         (
    #             "x.{func}('foo') or x.{func}('bar') or x.{func}('foo')",
    #             "x.{func}(('foo', 'bar'))",
    #         ),
    #         # 2 cst.SimpleStrings 2 cst.Tuple alternating
    #         (
    #             "x.{func}('a') or x.{func}(('b', 'c')) or x.{func}('d') or x.{func}(('e', 'f', 'g', 'h'))",
    #             "x.{func}(('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'))",
    #         ),
    #         # 10 cst.SimpleStrings
    #         (
    #             " or ".join("x.{func}" + f"({item[0]})" for item in _10_of_each_type),
    #             "x.{func}" + f"(({', '.join(item[0] for item in _10_of_each_type)}))",
    #         ),
    #         # 10 cst.ConcatenatedStrings
    #         (
    #             " or ".join("x.{func}" + f"({item[1]})" for item in _10_of_each_type),
    #             "x.{func}" + f"(({', '.join(item[1] for item in _10_of_each_type)}))",
    #         ),
    #         # 10 cst.FormattedStrings
    #         (
    #             " or ".join("x.{func}" + f"({item[2]})" for item in _10_of_each_type),
    #             "x.{func}" + f"(({', '.join(item[2] for item in _10_of_each_type)}))",
    #         ),
    #         # 10 cst.Names
    #         (
    #             " or ".join("x.{func}" + f"({item[3]})" for item in _10_of_each_type),
    #             "x.{func}" + f"(({', '.join(item[3] for item in _10_of_each_type)}))",
    #         ),
    #         # 10 cst.Tuples with all types
    #         (
    #             " or ".join(
    #                 "x.{func}" + f"(({', '.join(item)}))" for item in _10_of_each_type
    #             ),
    #             "x.{func}"
    #             + f"(({', '.join(', '.join(item) for item in _10_of_each_type)}))",
    #         ),
    #     ],
    # )
    # def test_more_than_two_calls(self, tmpdir, func, input_code, expected):
    #     self._format_func_run_test(
    #         tmpdir, func, input_code, expected, num_changes=input_code.count(" or ")
    #     )
