from codemodder.codemods.api import SemgrepCodemod, ReviewGuidance


class AddRequestsTimeouts(SemgrepCodemod):
    NAME = "add-requests-timeouts"
    SUMMARY = "Add timeout to `requests` calls"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    DESCRIPTION = "Add timeout to `requests` call"
    REFERENCES = [
        {
            "url": "https://docs.python-requests.org/en/master/user/quickstart/#timeouts",
            "description": "",
        },
    ]

    @classmethod
    def rule(cls):
        return """
        rules:
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

    # Sets an arbitrary default timeout for all requests
    DEFAULT_TIMEOUT = 60

    def on_result_found(self, original_node, updated_node):
        del original_node
        return self.add_arg_to_call(updated_node, "timeout", self.DEFAULT_TIMEOUT)
