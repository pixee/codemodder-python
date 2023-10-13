from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.api.helpers import NewArg


class HardenRuamel(SemgrepCodemod):
    NAME = "harden-ruamel"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    SUMMARY = "Use `typ='safe'` in ruamel.yaml() Calls"
    DESCRIPTION = "Ensures all unsafe calls to ruamel.yaml.YAML use `typ='safe'`."
    REFERENCES = [
        {
            "url": "https://owasp.org/www-community/vulnerabilities/Deserialization_of_untrusted_data",
            "description": "",
        }
    ]

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
        new_args = self.replace_args(
            original_node, [NewArg(name="typ", value='"safe"', add_if_missing=False)]
        )
        return self.update_arg_target(updated_node, new_args)
