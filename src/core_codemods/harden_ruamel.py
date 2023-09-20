from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class HardenRuamel(SemgrepCodemod):
    NAME = "harden-ruamel"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    SUMMARY = "Use safe YAML loading in ruamel.yaml"
    DESCRIPTION = "Ensures all unsafe calls to ruamel.yaml.YAML use `typ='safe'`."

    @classmethod
    def rule(cls):
        return """
            rules:
                - pattern-either:
                  - patterns:
                    - pattern: ruamel.yaml.YAML(typ="unsafe", ...)
                    - pattern-inside: |
                        import ruamel
                        ...
                  - patterns:
                    - pattern: ruamel.yaml.YAML(typ="base", ...)
                    - pattern-inside: |
                        import ruamel
                        ...

        """

    def on_result_found(self, original_node, updated_node):
        new_args = self.replace_arg(original_node, "typ", '"safe"')
        return self.update_arg_target(updated_node, new_args)
