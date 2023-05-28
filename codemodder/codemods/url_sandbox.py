import libcst as cst
from libcst import matchers
from libcst.codemod import VisitorBasedCodemodCommand


replacement_import = "safe_requests"


class UrlSandbox(VisitorBasedCodemodCommand):
    DESCRIPTION: str = (
        "Replaces request.{func} with more secure safe_request library functions."
    )

    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> cst.Import:
        if is_requests_import(original_node):
            return updated_node.with_changes(
                names=[
                    updated_node.names[0].with_changes(
                        name=updated_node.names[0].name.with_changes(
                            value=replacement_import
                        )
                    )
                ]
            )

        return updated_node

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:

        if is_requests_import(original_node):
            return updated_node.with_changes(
                module=updated_node.module.with_changes(value=replacement_import)
            )

        return updated_node

    def leave_Expr(self, original_node: cst.Expr, updated_node: cst.Expr) -> cst.Expr:
        if is_requests_get_node(original_node):
            updated_import_call = updated_node.value.func.value.with_changes(
                value=replacement_import
            )

            return updated_node.with_changes(
                value=updated_node.value.with_changes(
                    func=updated_node.value.func.with_changes(value=updated_import_call)
                )
            )

        return updated_node


def is_requests_get_node(node: cst.Expr) -> bool:
    """
    Check to see if either: requests.get() or get() is called.

    :param node:
    :return: bool
    """
    library_dot_get = matchers.Expr(
        value=matchers.Call(
            func=matchers.Attribute(
                value=matchers.Name(value="requests"), attr=matchers.Name(value="get")
            )
        )
    )

    return matchers.matches(
        node,
        library_dot_get,
    )


def is_requests_import(node: cst.Import | cst.ImportFrom) -> bool:
    import_alias_requests = matchers.ImportAlias(name=matchers.Name(value="requests"))
    import_alias_get = matchers.ImportAlias(name=matchers.Name(value="get"))

    direct_import = matchers.Import(names=[import_alias_requests])
    from_requests_import_get = matchers.ImportFrom(
        module=cst.Name(value="requests"), names=[import_alias_get]
    )

    return matchers.matches(
        node,
        matchers.OneOf(direct_import, from_requests_import_get),
    )
