import libcst as cst
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.utils_mixin import NameResolutionMixin


class WithThreadingLock(SemgrepCodemod, NameResolutionMixin):
    NAME = "bad-lock-with-statement"
    SUMMARY = "Separate Lock Instantiation from `with` Call"
    DESCRIPTION = (
        "Replace deprecated usage of threading lock classes as context managers."
    )
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    REFERENCES = [
        {
            "url": "https://pylint.pycqa.org/en/latest/user_guide/messages/warning/useless-with-lock.",
            "description": "",
        },
        {
            "url": "https://docs.python.org/3/library/threading.html#using-locks-conditions-and-semaphores-in-the-with-statement",
            "description": "",
        },
    ]

    @classmethod
    def rule(cls):
        return """
        rules:
          - patterns:
            - pattern: |
                with $BODY:
                    ...
            - metavariable-pattern:
                metavariable: $BODY
                patterns:
                - pattern-either:
                    - pattern: threading.Lock()
                    - pattern: threading.RLock()
                    - pattern: threading.Condition()
                    - pattern: threading.Semaphore()
                    - pattern: threading.BoundedSemaphore()
            - pattern-inside: |
                import threading
                ...
            - focus-metavariable: $BODY
        """

    def leave_With(self, original_node: cst.With, updated_node: cst.With):
        # We deliberately restrict ourselves to simple cases where there's only one with clause for now.
        # Semgrep appears to be insufficiently expressive to match multiple clauses correctly.
        # We should probably just rewrite this codemod using libcst without semgrep.
        if len(original_node.items) == 1 and self.node_is_selected(
            original_node.items[0]
        ):
            current_names = self.find_used_names_in_module()
            name_for_node_type = _get_node_name(original_node)
            # arbitrarily choose `name_cm` if `name` name is already taken
            # in hopes that `name_cm` is very unlikely to be used.
            value = (
                name_for_node_type
                if name_for_node_type not in current_names
                else f"{name_for_node_type}_cm"
            )
            name = cst.Name(value=value)
            assign = cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[cst.AssignTarget(target=name)],
                        value=updated_node.items[0].item,
                    )
                ]
            )
            # TODO: add result
            return cst.FlattenSentinel(
                [
                    assign,
                    updated_node.with_changes(
                        items=[cst.WithItem(name, asname=updated_node.items[0].asname)]
                    ),
                ]
            )

        return original_node


def _get_node_name(original_node: cst.With):
    func_call = original_node.items[0].item.func
    if isinstance(func_call, cst.Name):
        return func_call.value.lower()
    if isinstance(func_call, cst.Attribute):
        return func_call.attr.value.lower()
    return ""
