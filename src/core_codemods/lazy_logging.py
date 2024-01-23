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
    detector_pattern = """
        rules:
            - pattern-either:
              - patterns:
                - pattern: logging.$FUNC(..., ... % ..., ...)
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
                          - pattern: log
              - patterns:
                - pattern: logging.getLogger(...).$FUNC(..., ... % ..., ...)
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
                          - pattern: log
              - patterns:
                - pattern: $VAR.$FUNC(..., ... % ..., ...)
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
                          - pattern: log
        """

    def on_result_found(self, original_node, updated_node):
        del original_node
        match updated_node.func:
            case cst.Name(value="log") | cst.Attribute(attr=cst.Name(value="log")):
                # logging.log(INFO, ...), log(INFO, ...)
                first_arg = [updated_node.args[0]]
                remaining_args = list(updated_node.args[2:])
                format_string = updated_node.args[1].value.left
                format_args = updated_node.args[1].value.right
            case _:
                first_arg = []
                remaining_args = list(updated_node.args[1:])
                format_string = updated_node.args[0].value.left
                format_args = updated_node.args[0].value.right

        new_args = [cst.Arg(value=format_string)]
        if isinstance(format_args, cst.Tuple):
            for element in format_args.elements:
                new_args.append(cst.Arg(value=element.value))
        else:
            new_args.append(cst.Arg(value=format_args))
        return updated_node.with_changes(args=first_arg + new_args + remaining_args)
