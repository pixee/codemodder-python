from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.semgrep import SemgrepRuleDetector
from core_codemods.api import CoreCodemod, Metadata, Reference, ReviewGuidance


class TransformAddRequestsTimeouts(LibcstResultTransformer):
    # Sets an arbitrary default timeout for all requests
    DEFAULT_TIMEOUT = 60

    change_description = "Add timeout to `requests` call"

    def on_result_found(self, original_node, updated_node):
        del original_node
        return self.add_arg_to_call(updated_node, "timeout", self.DEFAULT_TIMEOUT)


# This codemod uses the lower level codemod and transformer APIs for the sake of example.
AddRequestsTimeouts = CoreCodemod(
    metadata=Metadata(
        name="add-requests-timeouts",
        summary="Add timeout to `requests` calls",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(
                url="https://docs.python-requests.org/en/master/user/quickstart/#timeouts"
            ),
        ],
    ),
    detector=SemgrepRuleDetector(
        """
        - patterns:
            - pattern-inside: |
                import requests
                ...
            - pattern: requests.$CALL(...)
            - pattern-not: requests.$CALL(..., timeout=$TIMEOUT, ...)
            - metavariable-pattern:
                metavariable: $CALL
                patterns:
                  - pattern-either:
                    - pattern: get
                    - pattern: post
                    - pattern: put
                    - pattern: delete
                    - pattern: head
                    - pattern: options
                    - pattern: patch
                    - pattern: request
        """
    ),
    transformer=LibcstTransformerPipeline(TransformAddRequestsTimeouts),
)
