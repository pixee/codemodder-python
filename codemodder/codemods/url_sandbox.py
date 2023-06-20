import libcst as cst
from libcst import Name

from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import PositionProvider
from codemodder.codemods.base_codemod import BaseCodemod
from codemodder.codemods.base_visitor import BaseVisitor

replacement_import = "safe_requests"


class UrlSandbox(BaseCodemod, BaseVisitor):
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
        BaseCodemod.__init__(self, results_by_id)
        BaseVisitor.__init__(self, context, self._results)

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if self.filter_by_result(original_node):
            AddImportsVisitor.add_needed_import(
                self.context, "security", "safe_requests"
            )
            RemoveImportsVisitor.remove_unused_import(self.context, "requests")
            return updated_node.with_changes(
                func=updated_node.func.with_changes(value=Name(replacement_import))
            )
        return updated_node
