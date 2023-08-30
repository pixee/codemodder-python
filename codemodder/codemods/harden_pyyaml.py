import libcst as cst
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class HardenPyyaml(SemgrepCodemod):
    NAME = "harden-pyyaml"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Ensures all calls to yaml.load use `SafeLoader`."

    @classmethod
    def rule(cls):
        return """
            rules:
              - id: harden-pyyaml
                pattern-either:
                  - patterns:
                      - pattern: yaml.load(...)
                      - pattern-inside: |
                          import yaml
                          ...
                          yaml.load(...,$ARG)
                      - metavariable-pattern:
                          metavariable: $ARG
                          patterns:
                            - pattern-not:
                                pattern: yaml.SafeLoader
                  - patterns:
                      - pattern: yaml.load(...)
                      - pattern-inside: |
                          import yaml
                          ...
                          yaml.load(...,Loader=$ARG)
                      - metavariable-pattern:
                          metavariable: $ARG
                          patterns:
                            - pattern-not:
                                pattern: yaml.SafeLoader

        """

    def on_result_found(self, _, updated_node):
        second_arg = cst.parse_expression("yaml.SafeLoader")
        new_args = [*updated_node.args[:1], second_arg]
        return self.update_arg_target(updated_node, new_args)
