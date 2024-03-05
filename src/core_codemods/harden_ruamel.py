from codemodder.codemods.libcst_transformer import NewArg
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class HardenRuamel(SimpleCodemod):
    metadata = Metadata(
        name="harden-ruamel",
        summary="Use `typ='safe'` in ruamel.yaml() Calls",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://owasp.org/www-community/vulnerabilities/Deserialization_of_untrusted_data"
            ),
        ],
    )
    change_description = (
        "Ensures all unsafe calls to ruamel.yaml.YAML use `typ='safe'`."
    )
    detector_pattern = """
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
