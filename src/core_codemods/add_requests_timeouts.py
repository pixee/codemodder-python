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

    # Sets an arbitrary default timeout for all requests
    DEFAULT_TIMEOUT = 60

    def on_result_found(self, original_node, updated_node):
        del original_node
        return self.add_arg_to_call(updated_node, "timeout", self.DEFAULT_TIMEOUT)
