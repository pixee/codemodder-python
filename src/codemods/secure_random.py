import libcst as cst
import libcst.matchers as matchers
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from codemods.helper import split_module


class SecureRandom(VisitorBasedCodemodCommand):
    DESCRIPTION: str = "Replaces random.random with secrets."

    def __init__(self, context: CodemodContext):
        super().__init__(context)

    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> cst.Import:
        if is_random_import(original_node):
            return cst.RemoveFromParent()

        return updated_node

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        (
            statements_before_imports,
            statements_until_add_imports,
            statements_after_imports,
        ) = split_module(original_node, updated_node)

        return updated_node.with_changes(
            body=[
                *statements_before_imports,
                *statements_until_add_imports,
                *[
                    cst.parse_statement(
                        "import secrets", config=updated_node.config_for_parsing
                    )
                ],
                *statements_after_imports,
            ]
        )

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if is_random_node(original_node):
            self.modified_random = True
            return updated_node.with_changes(func=cst.Name("secrets"))
        return updated_node


def is_random_node(node: cst.Call) -> bool:
    return matchers.matches(
        node,
        matchers.Call(func=matchers.Attribute(value=matchers.Name(value="random"))),
    )


def is_random_import(node: cst.Import) -> bool:
    import_alias = matchers.ImportAlias(name=matchers.Name(value="random"))
    return matchers.matches(node, matchers.Import(names=[import_alias]))
