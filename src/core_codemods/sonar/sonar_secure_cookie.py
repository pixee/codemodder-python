from codemodder.codemods.base_codemod import ToolRule
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from core_codemods.secure_cookie_mixin import SecureCookieMixin
from core_codemods.secure_flask_cookie import SecureFlaskCookie
from core_codemods.sonar.api import SonarCodemod

rules = [
    ToolRule(
        id="python:S3330",
        name='Creating cookies without the "HttpOnly" flag is security-sensitive',
        url="https://rules.sonarsource.com/python/RSPEC-3330/",
    ),
    ToolRule(
        id="python:S2092",
        name='Creating cookies without the "secure" flag is security-sensitive',
        url="https://rules.sonarsource.com/python/RSPEC-2092/",
    ),
]


class SonarSecureCookieTransformer(LibcstResultTransformer, SecureCookieMixin):
    change_description = "Flask response `set_cookie` call should be called with `secure=True`, `httponly=True`, and `samesite='Lax'`."

    def leave_Call(self, original_node, updated_node):
        if self.node_is_selected(original_node.func):
            self.report_change(original_node)
            new_args = self.replace_args(
                original_node, self._choose_new_args(original_node)
            )
            return self.update_arg_target(updated_node, new_args)
        return updated_node


SonarSecureCookie = SonarCodemod.from_core_codemod_with_multiple_rules(
    name="secure-cookie",
    other=SecureFlaskCookie,
    rules=rules,
    transformer=LibcstTransformerPipeline(SonarSecureCookieTransformer),
)
