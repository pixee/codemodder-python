from functools import wraps
from typing import Callable, TypeVar

import libcst as cst

from codemodder.codemods.base_visitor import BaseTransformer, BaseVisitor

# TypeVars for decorators below
_BaseVisitorOrTransformer = TypeVar(
    "_BaseVisitorOrTransformer", BaseVisitor, BaseTransformer
)
_CSTNode = TypeVar("_CSTNode", bound=cst.CSTNode)


def check_filter_by_path_includes_or_excludes(
    func: Callable[[_BaseVisitorOrTransformer, _CSTNode, _CSTNode], cst.CSTNode]
) -> Callable[[_BaseVisitorOrTransformer, _CSTNode, _CSTNode], cst.CSTNode]:
    """
    Decorator to filter nodes based on path-includes or path-excludes flags.

    Calls the decorated func only if the original node is not filtered.
    otherwise, returns the updated node as is.

    ```
    @check_filter_by_path_includes_or_excludes
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call
        # rest of the method
    ```

    Is equivalent to:

    ```
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call
        # Added by the decorator
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
            ):
            return updated_node

        # rest of the method
    ```
    """

    @wraps(func)
    def wrapper(
        instance: _BaseVisitorOrTransformer,
        original_node: _CSTNode,
        updated_node: _CSTNode,
    ) -> cst.CSTNode:
        if not instance.filter_by_path_includes_or_excludes(
            instance.node_position(original_node)
        ):
            return updated_node
        return func(instance, original_node, updated_node)

    return wrapper


def check_node_is_not_selected(
    func: Callable[[_BaseVisitorOrTransformer, _CSTNode, _CSTNode], cst.CSTNode]
) -> Callable[[_BaseVisitorOrTransformer, _CSTNode, _CSTNode], cst.CSTNode]:
    """
    Decorator to filter nodes based on whether the node is selected or not.

    Calls the decorated func only if the original node is not selected.
    otherwise, returns the updated node as is.

    ```
    @check_node_is_not_selected
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call
        # rest of the method
    ```

    Is equivalent to:

    ```
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call
        # Added by the decorator
        if not self.node_is_selected(original_node):
            return updated_node

        # rest of the method
    ```
    """

    @wraps(func)
    def wrapper(
        instance: _BaseVisitorOrTransformer,
        original_node: _CSTNode,
        updated_node: _CSTNode,
    ) -> cst.CSTNode:
        if not instance.node_is_selected(original_node):
            return updated_node
        return func(instance, original_node, updated_node)

    return wrapper
