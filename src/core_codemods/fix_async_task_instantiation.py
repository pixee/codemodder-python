from typing import Optional

import libcst as cst
from libcst import MaybeSentinel

from codemodder.codemods.utils import BaseType, infer_expression_type
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class FixAsyncTaskInstantiation(SimpleCodemod, NameAndAncestorResolutionMixin):
    metadata = Metadata(
        name="fix-async-task-instantiation",
        summary="Use High-Level `asyncio` API Functions to Create Tasks",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/asyncio-task.html#asyncio.Task"
            ),
        ],
    )
    change_description = "Replace instantiation of `asyncio.Task` with higher-level functions to create tasks."
    _module_name = "asyncio"

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        if self.find_base_name(original_node) != "asyncio.Task":
            return updated_node
        coroutine_arg = original_node.args[0]
        loop_arg, eager_start_arg, other_args = self._split_args(original_node.args[1:])

        loop_type = (
            infer_expression_type(self.resolve_expression(loop_arg.value))
            if loop_arg
            else None
        )

        if (
            infer_expression_type(self.resolve_expression(eager_start_arg.value))
            if eager_start_arg
            else None
        ) == BaseType.TRUE:
            if not loop_arg or self._is_invalid_loop_value(loop_type):
                # asking for eager_start without a loop or incorrectly setting loop is bad.
                # We won't do anything.
                return updated_node

            loop_arg = loop_arg.with_changes(keyword=None, equal=MaybeSentinel.DEFAULT)
            return self.node_eager_task(
                original_node,
                updated_node,
                replacement_args=[loop_arg, coroutine_arg] + other_args,
            )

        if loop_arg:
            if loop_type == BaseType.NONE:
                return self.node_create_task(
                    original_node,
                    updated_node,
                    replacement_args=[coroutine_arg] + other_args,
                )
            if self._is_invalid_loop_value(loop_type):
                # incorrectly assigned loop kwarg to something that is not a loop.
                # We won't do anything.
                return updated_node

            return self.node_loop_create_task(
                original_node, coroutine_arg, loop_arg, other_args
            )
        return self.node_create_task(
            original_node, updated_node, replacement_args=[coroutine_arg] + other_args
        )

    def node_create_task(
        self,
        original_node: cst.Call,
        updated_node: cst.Call,
        replacement_args=list[cst.Arg],
    ) -> cst.Call:
        """Convert `asyncio.Task(...)` to `asyncio.create_task(...)`"""
        self.report_change(original_node)
        maybe_name = self.get_aliased_prefix_name(original_node, self._module_name)
        if (maybe_name := maybe_name or self._module_name) == self._module_name:
            self.add_needed_import(self._module_name)
        self.remove_unused_import(original_node)

        if len(replacement_args) == 1:
            replacement_args[0] = replacement_args[0].with_changes(
                comma=MaybeSentinel.DEFAULT
            )
        return self.update_call_target(
            updated_node, maybe_name, "create_task", replacement_args=replacement_args
        )

    def node_eager_task(
        self,
        original_node: cst.Call,
        updated_node: cst.Call,
        replacement_args=list[cst.Arg],
    ) -> cst.Call:
        """Convert `asyncio.Task(...)` to `asyncio.eager_task_factory(loop, coro...)`"""
        self.report_change(original_node)
        maybe_name = self.get_aliased_prefix_name(original_node, self._module_name)
        if (maybe_name := maybe_name or self._module_name) == self._module_name:
            self.add_needed_import(self._module_name)
        self.remove_unused_import(original_node)
        return self.update_call_target(
            updated_node,
            maybe_name,
            "eager_task_factory",
            replacement_args=replacement_args,
        )

    def node_loop_create_task(
        self,
        original_node: cst.Call,
        coroutine_arg: cst.Arg,
        loop_arg: cst.Arg,
        other_args: list[cst.Arg],
    ) -> cst.Call:
        """Convert `asyncio.Task(..., loop=loop,...)` to `loop.create_task(...)`"""
        self.report_change(original_node)
        coroutine_arg = coroutine_arg.with_changes(comma=cst.MaybeSentinel.DEFAULT)
        loop_attr = loop_arg.value
        new_call = cst.Call(
            func=cst.Attribute(value=loop_attr, attr=cst.Name("create_task")),
            args=[coroutine_arg] + other_args,
        )
        self.remove_unused_import(original_node)
        return new_call

    def _split_args(
        self, args: list[cst.Arg]
    ) -> tuple[Optional[cst.Arg], Optional[cst.Arg], list[cst.Arg]]:
        """Find the loop kwarg and the eager_start kwarg from a list of args.
        Return any args or non-None kwargs.
        """
        loop_arg, eager_start_arg = None, None
        other_args = []
        for arg in args:
            match arg:
                case cst.Arg(keyword=cst.Name(value="loop")):
                    loop_arg = arg
                case cst.Arg(keyword=cst.Name(value="eager_start")):
                    eager_start_arg = arg
                case cst.Arg(keyword=cst.Name() as k) if k.value != "None":
                    # keep kwarg that are not set to None
                    other_args.append(arg)
                case cst.Arg(keyword=None):
                    # keep post args
                    other_args.append(arg)

        return loop_arg, eager_start_arg, other_args

    def _is_invalid_loop_value(self, loop_type):
        return loop_type in (
            BaseType.NONE,
            BaseType.NUMBER,
            BaseType.LIST,
            BaseType.STRING,
            BaseType.BYTES,
            BaseType.TRUE,
            BaseType.FALSE,
        )
