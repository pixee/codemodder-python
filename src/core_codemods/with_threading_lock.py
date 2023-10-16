import libcst as cst
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class WithThreadingLock(SemgrepCodemod):
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
            # TODO: how to avoid name conflicts here?
            name = cst.Name(value="lock")
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
