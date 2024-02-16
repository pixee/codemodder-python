import libcst as cst
import pytest
from codemodder.codemods.utils import BaseType, infer_expression_type


class TestBaseType:
    def test_binary_op_number(self):
        e = cst.parse_expression("1 + float(2)")
        assert infer_expression_type(e) == BaseType.NUMBER

    def test_binary_op_string_mixed(self):
        e = cst.parse_expression('f"a"+foo()')
        assert infer_expression_type(e) == BaseType.STRING

    def test_binary_op_list(self):
        e = cst.parse_expression("[1,2] + [x for x in [3]] + list((4,5))")
        assert infer_expression_type(e) == BaseType.LIST

    def test_binary_op_none(self):
        e = cst.parse_expression("foo() + bar()")
        assert infer_expression_type(e) == None

    def test_bytes(self):
        e = cst.parse_expression('b"123"')
        assert infer_expression_type(e) == BaseType.BYTES

    def test_if_mixed(self):
        e = cst.parse_expression('1 if True else "a"')
        assert infer_expression_type(e) == None

    def test_if_numbers(self):
        e = cst.parse_expression("abs(1) if True else 2")
        assert infer_expression_type(e) == BaseType.NUMBER

    def test_if_numbers2(self):
        e = cst.parse_expression("float(1) if True else len([1,2])")
        assert infer_expression_type(e) == BaseType.NUMBER

    @pytest.mark.parametrize("code", ["True", "False"])
    def test_bool(self, code):
        e = cst.parse_expression(code)
        if code == "True":
            assert infer_expression_type(e) == BaseType.TRUE
        else:
            assert infer_expression_type(e) == BaseType.FALSE

    def test_none(self):
        e = cst.parse_expression("None")
        assert infer_expression_type(e) == BaseType.NONE
