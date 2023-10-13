from typing import Sequence
from libcst import matchers
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import (
    PositionProvider,
)
from codemodder.codemods.base_codemod import (
    BaseCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.change import Change
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.file_context import FileContext
import libcst as cst
from libcst.codemod import (
    Codemod,
    CodemodContext,
    VisitorBasedCodemodCommand,
)


class HTTPSConnection(BaseCodemod, Codemod):
    METADATA = CodemodMetadata(
        DESCRIPTION="Enforce HTTPS Connection for urllib3",
        NAME="https-connection",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        REFERENCES=[
            {
                "url": "https://owasp.org/www-community/vulnerabilities/Insecure_Transport",
                "description": "",
            },
            {
                "url": "https://urllib3.readthedocs.io/en/stable/reference/urllib3.connectionpool.html#urllib3.HTTPConnectionPool",
                "description": "",
            },
        ],
    )
    CHANGE_DESCRIPTION = METADATA.DESCRIPTION
    SUMMARY = "Changes HTTPConnectionPool to HTTPSConnectionPool to enforce secure connection."

    METADATA_DEPENDENCIES = (PositionProvider,)

    matching_functions = {
        "urllib3.HTTPConnectionPool",
        "urllib3.connectionpool.HTTPConnectionPool",
    }

    def __init__(self, codemod_context: CodemodContext, *codemod_args):
        Codemod.__init__(self, codemod_context)
        BaseCodemod.__init__(self, *codemod_args)

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        visitor = ConnectionPollVisitor(self.context, self.file_context)
        result_tree = visitor.transform_module(tree)
        self.file_context.codemod_changes.extend(visitor.changes_in_file)
        return result_tree


class ConnectionPollVisitor(VisitorBasedCodemodCommand, NameResolutionMixin):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, codemod_context: CodemodContext, file_context: FileContext):
        super().__init__(codemod_context)
        self.line_exclude = file_context.line_exclude
        self.line_include = file_context.line_include
        self.changes_in_file: list[Change] = []

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        pos_to_match = self.node_position(original_node)
        line_number = pos_to_match.start.line
        if self.filter_by_path_includes_or_excludes(pos_to_match):
            true_name = self.find_base_name(original_node.func)
            if (
                self._is_direct_call_from_imported_module(original_node)
                and true_name in HTTPSConnection.matching_functions
            ):
                self.changes_in_file.append(
                    Change(
                        str(line_number), HTTPSConnection.CHANGE_DESCRIPTION
                    ).to_json()
                )
                # last argument _proxy_config does not match new method
                # we convert it to keyword
                new_args = list(original_node.args)
                if count_positional_args(original_node.args) == 10:
                    new_args[9] = new_args[9].with_changes(
                        keyword=cst.parse_expression("_proxy_config")
                    )
                # has a prefix, e.g. a.call() -> a.new_call()
                if matchers.matches(original_node.func, matchers.Attribute()):
                    return updated_node.with_changes(
                        args=new_args,
                        func=updated_node.func.with_changes(
                            attr=cst.parse_expression("HTTPSConnectionPool")
                        ),
                    )
                # it is a simple name, e.g. call() -> module.new_call()
                AddImportsVisitor.add_needed_import(self.context, "urllib3")
                RemoveImportsVisitor.remove_unused_import_by_node(
                    self.context, original_node
                )
                return updated_node.with_changes(
                    args=new_args,
                    func=cst.parse_expression("urllib3.HTTPSConnectionPool"),
                )
        return updated_node

    def filter_by_path_includes_or_excludes(self, pos_to_match):
        """
        Returns False if the node, whose position in the file is pos_to_match, matches any of the lines specified in the path-includes or path-excludes flags.
        """
        # excludes takes precedence if defined
        if self.line_exclude:
            return not any(match_line(pos_to_match, line) for line in self.line_exclude)
        if self.line_include:
            return any(match_line(pos_to_match, line) for line in self.line_include)
        return True

    def node_position(self, node):
        # See https://github.com/Instagram/LibCST/blob/main/libcst/_metadata_dependent.py#L112
        return self.get_metadata(PositionProvider, node)


def match_line(pos, line):
    return pos.start.line == line and pos.end.line == line


def count_positional_args(arglist: Sequence[cst.Arg]) -> int:
    for i, arg in enumerate(arglist):
        if arg.keyword:
            return i
    return len(arglist)
