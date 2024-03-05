from typing import Set, Tuple, Union

import libcst as cst
from libcst import matchers
from libcst.codemod import Codemod
from libcst.codemod.visitors import GatherUnusedImportsVisitor


class RemoveUnusedImportsCodemod(Codemod):
    """
    Removes unused imports. Combines GatherUnusedImportsVisitor and RemoveUnusedImportsTransformer.
    """

    METADATA_DEPENDENCIES = (*GatherUnusedImportsVisitor.METADATA_DEPENDENCIES,)

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        giv = GatherUnusedImportsVisitor(self.context)
        tree.visit(giv)
        return tree.visit(RemoveUnusedImportsTransformer(giv.unused_imports))


class RemoveUnusedImportsTransformer(cst.CSTTransformer):
    """
    Removes the unused imports from the unused_imports gathered by GatherUnusedImportsVisitor.
    """

    def __init__(
        self,
        unused_imports: Set[Tuple[cst.ImportAlias, Union[cst.Import, cst.ImportFrom]]],
    ) -> None:
        self.unused_imports = unused_imports

    def leave_import_alike(
        self,
        original_node: Union[cst.Import, cst.ImportFrom],
        updated_node: Union[cst.Import, cst.ImportFrom],
    ) -> Union[cst.Import, cst.ImportFrom, cst.RemovalSentinel]:
        new_aliases = [
            ia
            for ia in original_node.names
            if (ia, original_node) not in self.unused_imports
        ]
        if len(new_aliases) == 0:
            return cst.RemoveFromParent()
        if len(new_aliases) != len(original_node.names):
            # make no changes if all the aliases are there
            # make sure the last one has no comma
            new_aliases[-1] = new_aliases[-1].with_changes(
                comma=cst.MaybeSentinel.DEFAULT
            )
            return updated_node.with_changes(names=new_aliases)
        return updated_node

    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> cst.Import:
        # GatherUnusedImportsVisitor will never include a ImportStar, we skip those
        if matchers.matches(original_node.names, matchers.ImportStar()):
            return updated_node
        return self.leave_import_alike(original_node, updated_node)

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:
        if matchers.matches(original_node.names, matchers.ImportStar()):
            return updated_node
        return self.leave_import_alike(original_node, updated_node)
