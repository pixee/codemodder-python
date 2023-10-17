from typing import Sequence, Set

import libcst as cst
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import PositionProvider

from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import BaseCodemod
from codemodder.codemods.imported_call_modifier import ImportedCallModifier


class HTTPSConnectionModifier(ImportedCallModifier[Set[str]]):
    def updated_args(self, original_args):
        """
        Last argument _proxy_config does not match new method

        We convert it to keyword
        """
        new_args = list(original_args)
        if self.count_positional_args(new_args) == 10:
            new_args[9] = new_args[9].with_changes(
                keyword=cst.parse_expression("_proxy_config")
            )
        return new_args

    def update_attribute(self, true_name, original_node, updated_node, new_args):
        del true_name, original_node
        return updated_node.with_changes(
            args=new_args,
            func=updated_node.func.with_changes(
                attr=cst.Name(value="HTTPSConnectionPool")
            ),
        )

    def update_simple_name(self, true_name, original_node, updated_node, new_args):
        del true_name
        AddImportsVisitor.add_needed_import(self.context, "urllib3")
        RemoveImportsVisitor.remove_unused_import_by_node(self.context, original_node)
        return updated_node.with_changes(
            args=new_args,
            func=cst.parse_expression("urllib3.HTTPSConnectionPool"),
        )

    def count_positional_args(self, arglist: Sequence[cst.Arg]) -> int:
        for idx, arg in enumerate(arglist):
            if arg.keyword:
                return idx
        return len(arglist)


class HTTPSConnection(BaseCodemod):
    SUMMARY = "Enforce HTTPS Connection for `urllib3`"
    NAME = "https-connection"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    REFERENCES = [
        {
            "url": "https://owasp.org/www-community/vulnerabilities/Insecure_Transport",
            "description": "",
        },
        {
            "url": "https://urllib3.readthedocs.io/en/stable/reference/urllib3.connectionpool.html#urllib3.HTTPConnectionPool",
            "description": "",
        },
    ]

    METADATA_DEPENDENCIES = (PositionProvider,)

    matching_functions: set[str] = {
        "urllib3.HTTPConnectionPool",
        "urllib3.connectionpool.HTTPConnectionPool",
    }

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        visitor = HTTPSConnectionModifier(
            self.context,
            self.file_context,
            self.matching_functions,
            self.CHANGE_DESCRIPTION,
        )
        result_tree = visitor.transform_module(tree)
        self.file_context.codemod_changes.extend(visitor.changes_in_file)
        return result_tree
