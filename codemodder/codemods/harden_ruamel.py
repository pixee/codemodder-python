import libcst as cst
from libcst import matchers
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class HardenRuamel(SemgrepCodemod):
    NAME = "harden-ruamel"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
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
        new_args = make_new_args(original_node.args, target_arg="typ")
        return self.update_arg_target(updated_node, new_args)


def make_new_args(original_args, target_arg):
    new_args = []
    for arg in original_args:
        if matchers.matches(arg.keyword, matchers.Name(target_arg)):
            new = cst.Arg(
                keyword=cst.parse_expression("typ"),
                value=cst.parse_expression('"safe"'),
                equal=arg.equal,
            )
        else:
            new = arg
        new_args.append(new)
    return new_args
