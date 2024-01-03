from core_codemods.api import (
    CoreCodemod,
    Metadata,
    Reference,
    ReviewGuidance,
)
from codemodder.codemods.libcst_transformer import (
    LibcstTransformerPipeline,
    LibcstResultTransformer,
)
from codemodder.codemods.semgrep import SemgrepRuleDetector


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
            - pattern: $CALL(...)
            - pattern-not: $CALL(..., timeout=$TIMEOUT, ...)
            - metavariable-pattern:
                metavariable: $CALL
                patterns:
                  - pattern-either:
                    - pattern: requests.get
                    - pattern: requests.post
                    - pattern: requests.put
                    - pattern: requests.delete
                    - pattern: requests.head
                    - pattern: requests.options
                    - pattern: requests.patch
                    - pattern: requests.request
        """
    ),
    transformer=LibcstTransformerPipeline(TransformAddRequestsTimeouts),
)
