import libcst as cst
from libcst.codemod.visitors import GatherUnusedImportsVisitor
from libcst.metadata import (
    ParentNodeProvider,
    PositionProvider,
    QualifiedNameProvider,
    ScopeProvider,
)

from codemodder.codemods.check_annotations import is_disabled_by_annotations
from codemodder.codemods.transformations.remove_unused_imports import (
    RemoveUnusedImportsTransformer,
)
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod


class RemoveUnusedImports(SimpleCodemod):
    metadata = Metadata(
        name="unused-imports",
        summary="Remove Unused Imports",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )
    change_description = "Unused import."

    METADATA_DEPENDENCIES = (
        PositionProvider,
        ScopeProvider,
        QualifiedNameProvider,
        ParentNodeProvider,
    )

    IGNORE_ANNOTATIONS = ["unused-import", "F401", "W0611"]

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        # Do nothing in __init__.py files
        if self.file_context.file_path.name == "__init__.py":
            return tree
        gather_unused_visitor = GatherUnusedImportsVisitor(self.context)
        tree.visit(gather_unused_visitor)
        # filter the gathered imports by line excludes/includes
        filtered_unused_imports = set()
        for import_alias, importt in gather_unused_visitor.unused_imports:
            pos = self.get_metadata(PositionProvider, import_alias)
            if self.filter_by_path_includes_or_excludes(pos):
                if not is_disabled_by_annotations(
                    importt,
                    self.metadata,  # type: ignore
                    messages=self.IGNORE_ANNOTATIONS,
                ):
                    self.add_change_from_position(pos, self.change_description)
                    filtered_unused_imports.add((import_alias, importt))
        return tree.visit(RemoveUnusedImportsTransformer(filtered_unused_imports))

    def filter_by_path_includes_or_excludes(self, pos_to_match) -> bool:
        """
        Returns True if the node, whose position in the file is pos_to_match, matches any of the lines specified in the path-includes or path-excludes flags.
        """
        # excludes takes precedence if defined
        if self.line_exclude:
            return not any(match_line(pos_to_match, line) for line in self.line_exclude)
        if self.line_include:
            return any(match_line(pos_to_match, line) for line in self.line_include)
        return True


def match_line(pos, line):
    return pos.start.line == line and pos.end.line == line
