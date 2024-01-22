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
    logging_funcs = {"debug", "info", "warning", "error", "critical"}
    detector_pattern = """
        rules:
            - pattern-either:
              - patterns:
                - pattern: logging.$FUNC(... % ...)
                - pattern-inside: |
                    import logging
                    ...
                - metavariable-pattern:
                      metavariable: $FUNC
                      patterns:
                        - pattern-either:
                          - pattern: debug
                          - pattern: info
                          - pattern: warning
                          - pattern: error
                          - pattern: critical
              - patterns:
                - pattern: logging.getLogger(...).$FUNC(... % ...)
                - pattern-inside: |
                    import logging
                    ...
                - metavariable-pattern:
                      metavariable: $FUNC
                      patterns:
                        - pattern-either:
                          - pattern: debug
                          - pattern: info
                          - pattern: warning
                          - pattern: error
                          - pattern: critical
              - patterns:
                - pattern: $VAR.$FUNC(... % ...)
                - pattern-inside: |
                    import logging
                    ...
                    $VAR = logging.getLogger(...)
                    ...
                - metavariable-pattern:
                      metavariable: $FUNC
                      patterns:
                        - pattern-either:
                          - pattern: debug
                          - pattern: info
                          - pattern: warning
                          - pattern: error
                          - pattern: critical
        """

    def on_result_found(self, original_node, updated_node):
        # Extract the left side (format string) and right side (format args) of the modulo operation
        format_string = updated_node.args[0].value.left
        format_args = updated_node.args[0].value.right

        # Create a new list of arguments for the logging function
        new_args = [cst.Arg(value=format_string)]

        # If the right side is a Tuple, add each element as a separate argument
        if isinstance(format_args, cst.Tuple):
            for element in format_args.elements:
                new_args.append(cst.Arg(value=element.value))
        else:
            # Otherwise, add the single argument
            new_args.append(cst.Arg(value=format_args))

        return updated_node.with_changes(args=new_args)

    # def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
    #     # Match logging function calls with string formatting
    #     breakpoint()
    #     if (m.matches(updated_node.func, m.Attribute()) and
    #             isinstance(updated_node.func, cst.Attribute) and
    #             updated_node.func.attr.value in self.logging_funcs and
    #             # len(updated_node.args) == 1 and
    #             isinstance(updated_node.args[0].value, cst.BinaryOperation) and
    #             m.matches(updated_node.args[0].value.operator, m.Modulo())):
    #
    #         # Extract the left side (format string) and right side (format args) of the modulo operation
    #         format_string = updated_node.args[0].value.left
    #         format_args = updated_node.args[0].value.right
    #
    #         # Create a new list of arguments for the logging function
    #         new_args = [cst.Arg(value=format_string)]
    #
    #         # If the right side is a Tuple, add each element as a separate argument
    #         if isinstance(format_args, cst.Tuple):
    #             for element in format_args.elements:
    #                 new_args.append(cst.Arg(value=element.value))
    #         else:
    #             # Otherwise, add the single argument
    #             new_args.append(cst.Arg(value=format_args))
    #
    #         # Return the updated logging call
    #         self.report_change(original_node)
    #         return updated_node.with_changes(args=new_args)
    #
    #     return updated_node
