from typing import Optional

import libcst as cst

from codemodder.codemods.utils import BaseType, infer_expression_type
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod


class LazyLogging(SimpleCodemod, NameAndAncestorResolutionMixin):
    metadata = Metadata(
        name="lazy-logging",
        summary="Convert Eager Logging to Lazy Logging",
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
                      - pattern: warn
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
            - pattern: logging.$FUNC($MSG + ..., ...)
            {_pattern_inside}
            {_log_funcs}
          - patterns:
            - pattern: logging.getLogger(...).$FUNC($MSG + ..., ...)
            {_pattern_inside}
            {_log_funcs}
          - patterns:
            - pattern: $VAR.$FUNC($MSG + ..., ...)
            - pattern-inside: |
                import logging
                ...
                $VAR = logging.getLogger(...)
                ...
            {_log_funcs}
          - patterns:
            - pattern: logging.log($LEVEL, $MSG + ..., ...)
            {_pattern_inside}
          - patterns:
            - pattern: logging.getLogger(...).log($LEVEL, $MSG + ..., ...)
            {_pattern_inside}
          - patterns:
            - pattern: $VAR.log($LEVEL, $MSG + ..., ...)
            - pattern-inside: |
                import logging
                ...
                $VAR = logging.getLogger(...)
                ...
        """

    def on_result_found(self, original_node, updated_node):
        match updated_node.func:
            case cst.Name(value="log") | cst.Attribute(attr=cst.Name(value="log")):
                # logging.log(INFO, ...), log(INFO, ...)
                first_arg = [original_node.args[0]]
                remaining_args = list(original_node.args[2:])
                binop = original_node.args[1].value
            case _:
                first_arg = []
                remaining_args = list(original_node.args[1:])
                binop = original_node.args[0].value

        if set(self.all_operators(binop)) == {cst.Add, cst.Modulo}:
            # TODO: handle more complex case of str concat that uses both `%` and `+` operators
            return updated_node

        match binop.operator:
            case cst.Modulo():
                new_args = self.make_args_for_modulo(binop)
            case cst.Add():
                if (new_args := self.make_args_for_plus(binop)) is None:
                    return updated_node
        return updated_node.with_changes(args=first_arg + new_args + remaining_args)

    def make_args_for_plus(self, binop: cst.BinaryOperation) -> Optional[list[cst.Arg]]:
        if self.is_str_concat(binop):
            # Do not change explicit str concat, e.g.: `logging.info("one" + "two")
            return None

        if isinstance(binop.left, cst.SimpleString) and "%" in binop.left.value:
            # Do no change `logging.info("Something: %s " + var)` since intention is unclear
            return None
        left_type = infer_expression_type(self.resolve_expression(binop.left))
        right_type = infer_expression_type(self.resolve_expression(binop.right))
        if left_type != right_type or (type_both_sides := left_type) not in {
            BaseType.STRING,
            BaseType.BYTES,
        }:
            # Cannot concat different types.
            # Skip logging ints, etc. Eg: `logging.info(2+2)`
            return None

        format_strings, format_args, prefixes = self.process_concat(binop)
        if len(set(prefixes)) > 1:
            # TODO: handle more complex case of str concat with different prefixes, such as
            # `logging.info("one: " + r"two \\n" + u'three '+  four)`
            return None
        if prefixes:
            combined_format_string = cst.SimpleString(
                value=f"""{prefixes[0]}{"".join(format_strings)}\""""
            )
        else:
            combined_format_string = cst.SimpleString(
                value=f"""{'"' if type_both_sides == BaseType.STRING else ""}{"".join(format_strings)}\""""
            )
        return [cst.Arg(value=combined_format_string)] + format_args

    def make_args_for_modulo(self, binop: cst.BinaryOperation) -> list[cst.Arg]:
        format_string = binop.left
        format_args = binop.right
        new_args = [cst.Arg(value=format_string)]
        match format_args:
            case cst.Tuple():
                for element in format_args.elements:
                    new_args.append(cst.Arg(value=element.value))
            case _:
                new_args.append(cst.Arg(value=format_args))
        return new_args

    def all_operators(self, node: cst.BinaryOperation):
        if not isinstance(node.left, cst.BinaryOperation):
            return [node.operator.__class__]
        return [node.operator.__class__] + self.all_operators(node.left)

    def is_str_concat(self, node: cst.CSTNode) -> bool:
        match node:
            case cst.BinaryOperation(operator=cst.Add()):
                return self.is_str_concat(node.left) and self.is_str_concat(node.right)
        return isinstance(node, cst.SimpleString)

    def process_concat(
        self,
        node: cst.CSTNode,
        format_strings=None,
        format_args=None,
        prefixes=None,
    ) -> tuple[list[str], list[cst.Arg], list[str]]:
        if format_strings is None:
            format_strings = []
        if format_args is None:
            format_args = []
        if prefixes is None:
            prefixes = []

        match node:
            case cst.BinaryOperation(operator=cst.Add()):
                self.process_concat(node.left, format_strings, format_args, prefixes)
                self.process_concat(node.right, format_strings, format_args, prefixes)
            case cst.SimpleString():
                format_strings.append(node.raw_value)
                if node.prefix:
                    prefixes.append(node.prefix + '"')
            case _:
                format_strings.append("%s")
                format_args.append(cst.Arg(value=node))

        return format_strings, format_args, prefixes
