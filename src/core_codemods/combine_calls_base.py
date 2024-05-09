import libcst as cst
from libcst import matchers as m

from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import SimpleCodemod


class CombineCallsBaseCodemod(SimpleCodemod, NameResolutionMixin):
    combinable_funcs: list[str] = []
    dedupilcation_attr: str = "value"
    args_to_combine: list[int] = [0]
    args_to_keep_as_is: list[int] = []

    def leave_BooleanOperation(
        self, original_node: cst.BooleanOperation, updated_node: cst.BooleanOperation
    ) -> cst.CSTNode:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        for call_matcher in map(self.make_call_matcher, self.combinable_funcs):
            if self.matches_call_or_call(updated_node, call_matcher):
                self.report_change(original_node)
                return self.combine_calls(updated_node.left, updated_node.right)

            if self.matches_call_or_boolop(updated_node, call_matcher):
                self.report_change(original_node)
                return self.combine_call_or_boolop_fold_right(updated_node)

            if self.matches_boolop_or_call(updated_node, call_matcher):
                self.report_change(original_node)
                return self.combine_boolop_or_call_fold_left(updated_node)

        return updated_node

    def make_call_matcher(self, func_name: str) -> m.Call:
        raise NotImplementedError("Subclasses must implement this method")

    def check_calls_same_instance(
        self, left_call: cst.Call, right_call: cst.Call
    ) -> bool:
        raise NotImplementedError("Subclasses must implement this method")

    def matches_call_or_call(
        self, node: cst.BooleanOperation, call_matcher: m.Call
    ) -> bool:
        call_or_call = m.BooleanOperation(
            left=call_matcher, operator=m.Or(), right=call_matcher
        )
        # True if the node matches the pattern and the calls are the same instance
        return m.matches(node, call_or_call) and self.check_calls_same_instance(
            node.left, node.right
        )

    def matches_call_or_boolop(
        self, node: cst.BooleanOperation, call_matcher: m.Call
    ) -> bool:
        call_or_boolop = m.BooleanOperation(
            left=call_matcher,
            operator=m.Or(),
            right=m.BooleanOperation(left=call_matcher),
        )
        # True if the node matches the pattern and the calls are the same instance
        return m.matches(node, call_or_boolop) and self.check_calls_same_instance(
            node.left, node.right.left
        )

    def matches_boolop_or_call(
        self, node: cst.BooleanOperation, call_matcher: m.Call
    ) -> bool:
        boolop_or_call = m.BooleanOperation(
            left=m.BooleanOperation(right=call_matcher),
            operator=m.Or(),
            right=call_matcher,
        )
        # True if the node matches the pattern and the calls are the same instance
        return m.matches(node, boolop_or_call) and self.check_calls_same_instance(
            node.left.right, node.right
        )

    def combine_calls(self, *calls: cst.Call) -> cst.Call:
        first_call = calls[0]
        new_args = []
        for arg_index in sorted(self.args_to_keep_as_is + self.args_to_combine):
            if arg_index in self.args_to_combine:
                new_args.append(self.combine_args(*calls, arg_index=arg_index))
            else:
                new_args.append(first_call.args[arg_index])

        return cst.Call(func=first_call.func, args=new_args)

    def combine_args(self, *calls: cst.Call, arg_index: int) -> cst.Arg:
        elements = []
        seen_values = set()
        for call in calls:
            arg_value = call.args[arg_index].value
            arg_elements = (
                arg_value.elements
                if isinstance(arg_value, cst.Tuple)
                else (cst.Element(value=arg_value),)
            )

            for element in arg_elements:
                if (
                    value := getattr(element.value, self.dedupilcation_attr, None)
                ) in seen_values:
                    # If an element has a non-None value that has already been seen, continue to avoid duplicates
                    continue
                if value is not None:
                    seen_values.add(value)
                elements.append(element)

        return cst.Arg(value=cst.Tuple(elements=elements))

    def combine_call_or_boolop_fold_right(
        self, node: cst.BooleanOperation
    ) -> cst.BooleanOperation:
        new_left = self.combine_calls(node.left, node.right.left)
        new_right = node.right.right
        return cst.BooleanOperation(
            left=new_left, operator=node.right.operator, right=new_right
        )

    def combine_boolop_or_call_fold_left(
        self, node: cst.BooleanOperation
    ) -> cst.BooleanOperation:
        new_left = node.left.left
        new_right = self.combine_calls(node.left.right, node.right)
        return cst.BooleanOperation(
            left=new_left, operator=node.left.operator, right=new_right
        )
