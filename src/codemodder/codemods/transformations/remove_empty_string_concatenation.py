from typing import Union
import libcst as cst
from libcst import CSTTransformer, RemovalSentinel, SimpleString


class RemoveEmptyStringConcatenation(CSTTransformer):
    """
    Removes concatenation with empty strings (e.g. "hello " + "") or "hello" ""
    """

    def leave_FormattedStringExpression(
        self,
        original_node: cst.FormattedStringExpression,
        updated_node: cst.FormattedStringExpression,
    ) -> Union[
        cst.BaseFormattedStringContent,
        cst.FlattenSentinel[cst.BaseFormattedStringContent],
        RemovalSentinel,
    ]:
        expr = original_node.expression
        match expr:
            case SimpleString() if expr.raw_value == "":  # type: ignore
                return RemovalSentinel.REMOVE
        return updated_node

    def leave_BinaryOperation(
        self, original_node: cst.BinaryOperation, updated_node: cst.BinaryOperation
    ) -> cst.BaseExpression:
        return self.handle_node(updated_node)

    def leave_ConcatenatedString(
        self,
        original_node: cst.ConcatenatedString,
        updated_node: cst.ConcatenatedString,
    ) -> cst.BaseExpression:
        return self.handle_node(updated_node)

    def handle_node(
        self, updated_node: cst.BinaryOperation | cst.ConcatenatedString
    ) -> cst.BaseExpression:
        left = updated_node.left
        right = updated_node.right
        if self._is_empty_string_literal(left):
            if self._is_empty_string_literal(right):
                return cst.SimpleString(value='""')
            return right
        if self._is_empty_string_literal(right):
            if self._is_empty_string_literal(left):
                return cst.SimpleString(value='""')
            return left
        return updated_node

    def _is_empty_string_literal(self, node):
        match node:
            case cst.SimpleString() if node.raw_value == "":
                return True
            case cst.FormattedString() if not node.parts:
                return True
        return False
