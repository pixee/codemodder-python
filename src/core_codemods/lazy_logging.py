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
                - pattern: logging.$FUNC(... % ..., ...)
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
                - pattern: logging.getLogger(...).$FUNC(... % ..., ...)
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
                - pattern: $VAR.$FUNC(... % ..., ...)
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
        del original_node
        format_string = updated_node.args[0].value.left
        format_args = updated_node.args[0].value.right

        new_args = [cst.Arg(value=format_string)]
        if isinstance(format_args, cst.Tuple):
            for element in format_args.elements:
                new_args.append(cst.Arg(value=element.value))
        else:
            new_args.append(cst.Arg(value=format_args))
        return updated_node.with_changes(args=new_args + list(updated_node.args[1:]))
