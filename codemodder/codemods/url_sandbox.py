import itertools
import libcst as cst
from libcst import Name, matchers
from libcst.codemod import VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import PositionProvider
from codemodder.codemods.base_codemod import BaseCodemod

replacement_import = "safe_requests"


class UrlSandbox(BaseCodemod, VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (PositionProvider,)

    NAME = "url-sandbox"
    DESCRIPTION = (
        "Replaces request.{func} with more secure safe_request library functions."
    )
    AUTHOR = "dani.alcala@pixee.ai"
    YAML_FILES = [
        "sandbox_url_creation.yaml",
    ]
    # TODO may be recovered by the yaml files themselves
    RULE_IDS = [
        "sandbox-url-creation",
    ]

    def __init__(self, context, results_by_id):
        super(VisitorBasedCodemodCommand, self).__init__(context)
        self.__results = list(
            itertools.chain.from_iterable(
                map(lambda rId: results_by_id[rId], self.RULE_IDS)
            )
        )

    @property
    def results(self):
        return self.__results

    def filter_by_result(self, node):
        pos = self.get_metadata(PositionProvider, node)
        all_pos = map(extract_pos_from_result, self.results)
        return any(match_pos(pos, x) for x in all_pos)

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        pos = self.get_metadata(PositionProvider, original_node)
        if self.filter_by_result(original_node) and is_requests_get_call(original_node):
            AddImportsVisitor.add_needed_import(
                self.context, "security", "safe_requests"
            )
            RemoveImportsVisitor.remove_unused_import(self.context, "requests")
            return updated_node.with_changes(
                func=updated_node.func.with_changes(value=Name(replacement_import))
            )
        return updated_node


def match_pos(pos, x):
    # needs some leeway because the semgrep and libcst won't exactly match
    return (
        pos.start.line == x[0]
        and (pos.start.column in (x[1] - 1, x[1]))
        and pos.end.line == x[2]
        and (pos.end.column in (x[3] - 1, x[3]))
    )


def extract_pos_from_result(result):
    region = result["locations"][0]["physicalLocation"]["region"]
    # TODO it may be the case some of these attributes do not exist
    return (
        region.get("startLine"),
        region["startColumn"],
        region.get("endLine") or region.get("startLine"),
        region["endColumn"],
    )


# TODO having a proper module for these may be quite useful
def is_requests_get_call(node: cst.Call) -> bool:
    matches_requests_get_call = matchers.Call(
        func=matchers.Attribute(
            value=matchers.Name(value="requests"), attr=matchers.Name(value="get")
        )
    )
    return matchers.matches(node, matches_requests_get_call)


def is_requests_get_node(node: cst.Expr) -> bool:
    """
    Check to see if either: requests.get() or get() is called.

    :param node:
    :return: bool
    """
    library_dot_get = matchers.Expr(
        value=matchers.Call(
            func=matchers.Attribute(
                value=matchers.Name(value="requests"), attr=matchers.Name(value="get")
            )
        )
    )

    return matchers.matches(
        node,
        library_dot_get,
    )
