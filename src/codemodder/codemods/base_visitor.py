from typing import Any, Tuple
from libcst.codemod import ContextAwareVisitor, VisitorBasedCodemodCommand
from libcst.metadata import PositionProvider

from codemodder.result import Result


class UtilsMixin:
    results: list[Result]

    def __init__(self, results: list[Result]):
        self.results = results

    def filter_by_result(self, pos_to_match):
        return any(
            location.match(pos_to_match)
            for result in self.results
            for location in result.locations
        )

    def filter_by_path_includes_or_excludes(self, pos_to_match):
        """
        Returns True if the node, whose position in the file is pos_to_match, matches any of the lines specified in the path-includes or path-excludes flags.
        """
        # excludes takes precedence if defined
        if self.line_exclude:
            return not any(match_line(pos_to_match, line) for line in self.line_exclude)
        if self.line_include:
            return any(match_line(pos_to_match, line) for line in self.line_include)
        return True

    def node_is_selected(self, node) -> bool:
        if not self.results:
            return False

        pos_to_match = self.node_position(node)
        return self.filter_by_result(
            pos_to_match
        ) and self.filter_by_path_includes_or_excludes(pos_to_match)

    def node_position(self, node):
        # See https://github.com/Instagram/LibCST/blob/main/libcst/_metadata_dependent.py#L112
        return self.get_metadata(self.METADATA_DEPENDENCIES[0], node)

    def lineno_for_node(self, node):
        return self.node_position(node).start.line


class BaseTransformer(VisitorBasedCodemodCommand, UtilsMixin):
    METADATA_DEPENDENCIES: Tuple[Any, ...] = (PositionProvider,)

    def __init__(self, context, results: list[Result]):
        super().__init__(context)
        UtilsMixin.__init__(self, results)


class BaseVisitor(ContextAwareVisitor, UtilsMixin):
    METADATA_DEPENDENCIES: Tuple[Any, ...] = (PositionProvider,)

    def __init__(self, context, results: list[Result]):
        super().__init__(context)
        UtilsMixin.__init__(self, results)


def match_line(pos, line):
    return pos.start.line == line and pos.end.line == line
