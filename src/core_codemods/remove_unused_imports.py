import libcst as cst
from libcst.codemod import Codemod, CodemodContext
from libcst.codemod.visitors import GatherUnusedImportsVisitor
from libcst.metadata import (
    PositionProvider,
    QualifiedNameProvider,
    ScopeProvider,
    ParentNodeProvider,
)
from codemodder.codemods.base_codemod import (
    BaseCodemod,
    CodemodMetadata,
    ReviewGuidance,
)

from codemodder.change import Change
from codemodder.codemods.check_annotations import is_disabled_by_annotations
from codemodder.codemods.transformations.remove_unused_imports import (
    RemoveUnusedImportsTransformer,
)


class RemoveUnusedImports(BaseCodemod, Codemod):
    METADATA = CodemodMetadata(
        DESCRIPTION=("Remove unused imports from a module."),
        NAME="unused-imports",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        REFERENCES=[],
    )
    SUMMARY = "Remove Unused Imports"
    CHANGE_DESCRIPTION = "Unused import."

    METADATA_DEPENDENCIES = (
        PositionProvider,
        ScopeProvider,
        QualifiedNameProvider,
        ParentNodeProvider,
    )
    IGNORE_ANNOTATIONS = ["unused-import", "F401", "W0611"]

    def __init__(self, codemod_context: CodemodContext, *codemod_args):
        Codemod.__init__(self, codemod_context)
        BaseCodemod.__init__(self, *codemod_args)

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
                    self.file_context.codemod_changes.append(
                        Change(pos.start.line, self.CHANGE_DESCRIPTION)
                    )
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
