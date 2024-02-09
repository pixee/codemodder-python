import libcst as cst
from typing import Optional
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod, Reference
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from codemodder.codemods.utils import BaseType, infer_expression_type


class FixTaskInstantiation(SimpleCodemod, NameAndAncestorResolutionMixin):
    metadata = Metadata(
        name="fix-task-instantiation",
        summary="Use high-level `asyncio.create_task` API",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/asyncio-task.html#asyncio.Task"
            ),
        ],
    )
    change_description = "Replace instantiation of `asyncio.Task` with `create_task`"
    _module_name = "asyncio"

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        if self.find_base_name(original_node) == "asyncio.Task":
            loop_arg, other_args = self._find_loop_arg(original_node)
            if loop_arg:
                loop_type = infer_expression_type(
                    self.resolve_expression(loop_arg.value)
                )
                if loop_type == BaseType.NONE:
                    return self.node_create_task(original_node, updated_node)
                if loop_type in (
                    BaseType.NUMBER,
                    BaseType.LIST,
                    BaseType.STRING,
                    BaseType.BYTES,
                    BaseType.BOOL,
                ):
                    # incorrectly assigned loop kwarg to something that is not a loop.
                    # We won't do anything.
                    return updated_node

                coroutine_arg = original_node.args[0]
                return self.node_loop_create_task(
                    original_node, coroutine_arg, loop_arg, other_args
                )
            return self.node_create_task(original_node, updated_node)
        return updated_node

    def node_create_task(
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.Call:
        """Convert `asyncio.Task(...)` to `asyncio.create_task(...)`"""
        self.report_change(original_node)
        maybe_name = self.get_aliased_prefix_name(original_node, self._module_name)
        if (maybe_name := maybe_name or self._module_name) == self._module_name:
            self.add_needed_import(self._module_name)
        self.remove_unused_import(original_node)
        return self.update_call_target(updated_node, maybe_name, "create_task")

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

    def _find_loop_arg(self, node: cst.Call) -> tuple[Optional[cst.Arg], list[cst.Arg]]:
        """Find the loop kwarg from a call to `asyncio.Task(...)`
        First arg is always the coroutine so we ignore it.
        """
        loop_arg = None
        other_args = []
        for arg in node.args[1:]:
            match arg:
                case cst.Arg(keyword=cst.Name(value="loop")):
                    loop_arg = arg
                case _:
                    other_args.append(arg)

        return loop_arg, other_args
