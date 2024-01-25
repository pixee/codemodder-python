import libcst as cst
from libcst import matchers as m
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod


class LazyLogging(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="lazy-logging",
        summary="Simplify Boolean Expressions Using `startswith` and `endswith`",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[],
    )
    change_description = "Use lazy logging"
    # Weird-looking indentation is required for semgrep to run correctly.
    _pattern_inside = """\
- pattern-inside: |
                import logging
                ...
"""
    _log_funcs = """\
- metavariable-pattern:
                  metavariable: $FUNC
                  patterns:
                    - pattern-either:
                      - pattern: debug
                      - pattern: info
                      - pattern: warning
                      - pattern: error
                      - pattern: critical
                      - pattern: log
"""
    detector_pattern = f"""
    rules:
        - pattern-either:
          - patterns:
            - pattern: logging.$FUNC(..., ... % ..., ...)
            {_pattern_inside}
            {_log_funcs}
          - patterns:
            - pattern: logging.getLogger(...).$FUNC(..., ... % ..., ...)
            {_pattern_inside}
            {_log_funcs}
          - patterns:
            - pattern: $VAR.$FUNC(..., ... % ..., ...)
            - pattern-inside: |
                import logging
                ...
                $VAR = logging.getLogger(...)
                ...
            {_log_funcs}
          - patterns:
            - pattern: logging.$FUNC(..., $ANYTHING + ..., ...)
            {_pattern_inside}
            {_log_funcs}
          - patterns:
            - pattern: logging.getLogger(...).$FUNC(..., $ANYTHING + ..., ...)
            {_pattern_inside}
            {_log_funcs}
          - patterns:
            - pattern: $VAR.$FUNC(..., $ANYTHING + ..., ...)
            - pattern-inside: |
                import logging
                ...
                $VAR = logging.getLogger(...)
                ...
            {_log_funcs}
        """

    def on_result_found(self, original_node, updated_node):
        del original_node

        match updated_node.func:
            case cst.Name(value="log") | cst.Attribute(attr=cst.Name(value="log")):
                # logging.log(INFO, ...), log(INFO, ...)
                first_arg = [updated_node.args[0]]
                remaining_args = list(updated_node.args[2:])
                binop = updated_node.args[1].value
            case _:
                first_arg = []
                remaining_args = list(updated_node.args[1:])
                binop = updated_node.args[0].value

        if set(self.all_operators(binop)) == {cst.Add, cst.Modulo}:
            # TODO: handle more complex case of str concat that uses both `%` and `+` operators
            return updated_node

        match binop.operator:
            case cst.Modulo():
                format_string = binop.left
                format_args = binop.right
                new_args = [cst.Arg(value=format_string)]
                if isinstance(format_args, cst.Tuple):
                    for element in format_args.elements:
                        new_args.append(cst.Arg(value=element.value))
                else:
                    new_args.append(cst.Arg(value=format_args))
            case cst.Add():
                if self.has_non_literal(binop):
                    format_string, format_args = self.process_concat(binop)
                    combined_format_string = cst.SimpleString(
                        value='"' + "".join(format_string) + '"'
                    )
                    new_args = [cst.Arg(value=combined_format_string)] + format_args
                else:
                    return updated_node
        return updated_node.with_changes(args=first_arg + new_args + remaining_args)

    def all_operators(self, node: cst.BinaryOperation):
        if not isinstance(node.left, cst.BinaryOperation):
            return [node.operator.__class__]
        return [node.operator.__class__] + self.all_operators(node.left)

    def has_non_literal(self, node):
        # Check if the node is a binary operation
        if isinstance(node, cst.BinaryOperation) and m.matches(node.operator, m.Add()):
            return self.has_non_literal(node.left) or self.has_non_literal(node.right)
        # Return True if the node is not a string literal
        return not isinstance(node, cst.SimpleString)

    def process_concat(self, node: cst.CSTNode, format_string=None, format_args=None):
        if format_string is None:
            format_string = []
        if format_args is None:
            format_args = []

        # Recursive case: process the left and right sides
        # todo: change to match/ case
        if isinstance(node, cst.BinaryOperation) and m.matches(node.operator, m.Add()):
            self.process_concat(node.left, format_string, format_args)
            self.process_concat(node.right, format_string, format_args)
        else:
            # Check if the node is a string literal
            if isinstance(node, cst.SimpleString):
                format_string.append(node.value.strip("\"'"))
            else:
                format_string.append("%s")
                format_args.append(cst.Arg(value=node))

        return format_string, format_args
