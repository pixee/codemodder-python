import libcst as cst
from libcst import matchers
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class JwtDecodeVerify(SemgrepCodemod):
    NAME = "jwt-decode-verify"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Makes any of the multiple `verify` parameters to a `jwt.decode` call be `True`."

    @classmethod
    def rule(cls):
        return r"""
            rules:
                - pattern-either:
                  - patterns:
                      - pattern: jwt.decode(..., verify=False, ...)
                      - pattern-inside: |
                          import jwt
                          ...
                  - patterns:
                      - pattern-regex:  |-
                            jwt.decode\(.*options={.*"verify_(signature|exp|nbf|iat|aud|iss)": False.*}.*\)
                      - pattern-inside: |
                          import jwt
                          ...
        """

    def _replace_opts_dict(self, opts_dict):
        new_dict_elements = []

        for element in opts_dict.elements:
            if is_verify_keyword(element):
                new_el = cst.DictElement(
                    key=cst.parse_expression(element.key.value),
                    value=cst.parse_expression("True"),
                )
            else:
                new_el = element
            new_dict_elements.append(new_el)
        return new_dict_elements

    def replace_options_arg(self, node_args):
        new_args = []
        for arg in node_args:
            if matchers.matches(arg.keyword, matchers.Name("options")) and isinstance(
                opts_dict := arg.value, cst.Dict
            ):
                new_dict_elements = self._replace_opts_dict(opts_dict)
                new = cst.Arg(
                    keyword=cst.parse_expression("options"),
                    value=cst.Dict(
                        elements=new_dict_elements,
                    ),
                    equal=arg.equal,
                )
            else:
                new = arg
            new_args.append(new)
        return new_args

    def replace_arg(self, original_node, target_arg_name, target_arg_replacement_val):
        new_args = super().replace_arg(original_node, "verify", "True")
        return self.replace_options_arg(new_args)

    def on_result_found(self, original_node, updated_node):
        new_args = self.replace_arg(original_node, "verify", "True")
        return self.update_arg_target(updated_node, new_args)


def is_verify_keyword(element: cst.DictElement) -> bool:
    """Determine if DictElement is something like:
        DictElement(
            key=SimpleString(
                value='"verify_signature"',
                lpar=[],
                rpar=[],
            )
            ...
    where value should be anything with the word `verify`
    """
    return (
        matchers.matches(element.key, matchers.SimpleString())
        and "verify" in element.key.value
    )
