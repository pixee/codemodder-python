from libcst import matchers

from codemodder.codemods.libcst_transformer import NewArg


class SecureCookieMixin:
    def _choose_new_args(self, original_node):
        new_args = [
            NewArg(name="secure", value="True", add_if_missing=True),
            NewArg(name="httponly", value="True", add_if_missing=True),
        ]

        samesite = matchers.Arg(
            keyword=matchers.Name(value="samesite"),
            value=matchers.SimpleString(value="'Strict'"),
        )

        # samesite=Strict is OK because it's more restrictive than Lax.
        if not any(matchers.matches(arg, samesite) for arg in original_node.args):
            new_args.append(
                NewArg(name="samesite", value="'Lax'", add_if_missing=True),
            )

        return new_args
