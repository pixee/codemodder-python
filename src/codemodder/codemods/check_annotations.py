import re
from typing import Mapping

import libcst as cst
from libcst import CSTVisitor
from libcst._nodes.base import CSTNode  # noqa: F401
from libcst.metadata import ParentNodeProvider
from libcst.metadata.base_provider import ProviderT  # noqa: F401
from pylint.utils.pragma_parser import parse_pragma

NOQA_PATTERN = re.compile(r"^#\s*noqa(:\s+[A-Z]+[A-Z0-9]+)?", re.IGNORECASE)


__all__ = ["is_disabled_by_annotations"]


class _GatherCommentNodes(CSTVisitor):
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    messages: list[str]

    def __init__(
        self,
        metadata: Mapping[ProviderT, Mapping[CSTNode, object]],
        messages: list[str],
    ) -> None:
        self.comments: list[cst.Comment] = []
        super().__init__()
        self.metadata = metadata
        self.messages = messages

    def leave_Comment(self, original_node: cst.Comment) -> None:
        self.comments.append(original_node)

    def _process_simple_statement_line(self, stmt: cst.SimpleStatementLine) -> bool:
        # has a trailing comment string anywhere in the node
        stmt.body[0].visit(self)
        # has a trailing comment string anywhere in the node
        if stmt.trailing_whitespace.comment:
            self.comments.append(stmt.trailing_whitespace.comment)

        for comment in self.comments:
            trailing_comment_string = comment.value
            if trailing_comment_string and self._noqa_message_match(
                trailing_comment_string
            ):
                return True
            if trailing_comment_string and self._is_pylint_disable_unused_imports(
                trailing_comment_string
            ):
                return True

        # has a comment right above it
        match stmt:
            case cst.SimpleStatementLine(
                leading_lines=[
                    *_,
                    cst.EmptyLine(comment=cst.Comment(value=comment_string)),
                ]
            ):
                return self._noqa_message_match(comment_string) or (
                    self._is_pylint_disable_next_unused_imports(comment_string)
                )

        return False

    def is_disabled_by_linter(self, node: cst.CSTNode) -> bool:
        """
        Check if the import has a #noqa or # pylint: disable(-next) comment attached to it.
        """
        match self.get_metadata(ParentNodeProvider, node):
            case cst.SimpleStatementLine() as stmt:
                return self._process_simple_statement_line(stmt)
            case cst.Expr() as expr:
                match self.get_metadata(ParentNodeProvider, expr):
                    case cst.SimpleStatementLine() as stmt:
                        return self._process_simple_statement_line(stmt)
        return False

    def _noqa_message_match(self, comment: str) -> bool:
        if not (match := NOQA_PATTERN.match(comment)):
            return False

        if match.group(1):
            return match.group(1).strip(":").strip() in self.messages

        return True

    def _is_pylint_disable_unused_imports(self, comment: str) -> bool:
        # If pragma parse fails, ignore
        try:
            parsed = parse_pragma(comment)
            for p in parsed:
                if p.action == "disable" and any(
                    message in p.messages for message in self.messages
                ):
                    return True
        except Exception:
            pass
        return False

    def _is_pylint_disable_next_unused_imports(self, comment: str) -> bool:
        # If pragma parse fails, ignore
        try:
            parsed = parse_pragma(comment)
            for p in parsed:
                if p.action == "disable-next" and any(
                    message in p.messages for message in self.messages
                ):
                    return True
        except Exception:
            pass
        return False


def is_disabled_by_annotations(
    node: cst.CSTNode,
    metadata: Mapping[ProviderT, Mapping[CSTNode, object]],
    messages: list[str],
) -> bool:
    """
    Check if the import has a #noqa or # pylint: disable(-next) comment attached to it.
    """
    visitor = _GatherCommentNodes(metadata, messages)
    node.visit(visitor)
    return visitor.is_disabled_by_linter(node)
