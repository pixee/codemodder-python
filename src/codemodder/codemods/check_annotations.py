import re
from typing import Mapping

import libcst as cst
from libcst import CSTVisitor, ensure_type, matchers
from libcst.metadata import ParentNodeProvider
from libcst.metadata.base_provider import ProviderT  # noqa: F401
from libcst._nodes.base import CSTNode  # noqa: F401

from pylint.utils.pragma_parser import parse_pragma

NOQA_PATTERN = re.compile(r"^#\s*noqa", re.IGNORECASE)


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

    def _is_disabled_by_linter(self, node: cst.CSTNode) -> bool:
        """
        Check if the import has a #noqa or # pylint: disable(-next)=unused_imports comment attached to it.
        """
        match self.get_metadata(ParentNodeProvider, node):
            case cst.SimpleStatementLine() as parent:
                stmt = ensure_type(parent, cst.SimpleStatementLine)

                # has a trailing comment string anywhere in the node
                stmt.body[0].visit(self)
                # has a trailing comment string anywhere in the node
                if stmt.trailing_whitespace.comment:
                    self.comments.append(stmt.trailing_whitespace.comment)

                for comment in self.comments:
                    trailing_comment_string = comment.value
                    if trailing_comment_string and NOQA_PATTERN.match(
                        trailing_comment_string
                    ):
                        return True
                    if (
                        trailing_comment_string
                        and self._is_pylint_disable_unused_imports(
                            trailing_comment_string
                        )
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
                    if comment_string and self._is_pylint_disable_next_unused_imports(
                        comment_string
                    ):
                        return True
        return False

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
    Check if the import has a #noqa or # pylint: disable(-next)=unused_imports comment attached to it.
    """
    visitor = _GatherCommentNodes(metadata, messages)
    node.visit(visitor)
    return visitor._is_disabled_by_linter(node)
