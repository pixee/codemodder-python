from libcst import CSTVisitor, ensure_type, matchers
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
from codemodder.codemods.transformations.remove_unused_imports import (
    RemoveUnusedImportsTransformer,
)
import libcst as cst
from libcst.codemod import Codemod, CodemodContext
import re
from pylint.utils.pragma_parser import parse_pragma

NOQA_PATTERN = re.compile(r"^#\s*noqa", re.IGNORECASE)


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
                if not self._is_disabled_by_linter(importt):
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

    def _is_disabled_by_linter(self, node: cst.CSTNode) -> bool:
        """
        Check if the import has a #noqa or # pylint: disable(-next)=unused_imports comment attached to it.
        """
        parent = self.get_metadata(ParentNodeProvider, node)
        if parent and matchers.matches(parent, matchers.SimpleStatementLine()):
            stmt = ensure_type(parent, cst.SimpleStatementLine)

            # has a trailing comment string anywhere in the node
            comments_visitor = GatherCommentNodes()
            stmt.body[0].visit(comments_visitor)
            # has a trailing comment string anywhere in the node
            if stmt.trailing_whitespace.comment:
                comments_visitor.comments.append(stmt.trailing_whitespace.comment)

            for comment in comments_visitor.comments:
                trailing_comment_string = comment.value
                if trailing_comment_string and NOQA_PATTERN.match(
                    trailing_comment_string
                ):
                    return True
                if trailing_comment_string and _is_pylint_disable_unused_imports(
                    trailing_comment_string
                ):
                    return True

            # has a comment right above it
            if matchers.matches(
                stmt,
                matchers.SimpleStatementLine(
                    leading_lines=[
                        matchers.ZeroOrMore(),
                        matchers.EmptyLine(comment=matchers.Comment()),
                    ]
                ),
            ):
                comment_string = stmt.leading_lines[-1].comment.value
                if NOQA_PATTERN.match(comment_string):
                    return True
                if comment_string and _is_pylint_disable_next_unused_imports(
                    comment_string
                ):
                    return True
        return False


class GatherCommentNodes(CSTVisitor):
    def __init__(self) -> None:
        self.comments: list[cst.Comment] = []
        super().__init__()

    def leave_Comment(self, original_node: cst.Comment) -> None:
        self.comments.append(original_node)


def match_line(pos, line):
    return pos.start.line == line and pos.end.line == line


def _is_pylint_disable_unused_imports(comment: str) -> bool:
    # If pragma parse fails, ignore
    try:
        parsed = parse_pragma(comment)
        for p in parsed:
            if p.action == "disable" and (
                "unused-import" in p.messages or "W0611" in p.messages
            ):
                return True
    except Exception:
        pass
    return False


def _is_pylint_disable_next_unused_imports(comment: str) -> bool:
    # If pragma parse fails, ignore
    try:
        parsed = parse_pragma(comment)
        for p in parsed:
            if p.action == "disable-next" and (
                "unused-import" in p.messages or "W0611" in p.messages
            ):
                return True
    except Exception:
        pass
    return False
