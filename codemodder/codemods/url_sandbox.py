import libcst as cst
from libcst import Name
from codemodder.semgrep import rule_ids_from_yaml_files

from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from codemodder.codemods.change import Change
from codemodder.codemods.base_codemod import BaseCodemod
from codemodder.codemods.base_visitor import BaseVisitor

replacement_import = "safe_requests"


class UrlSandbox(BaseCodemod, BaseVisitor):
    NAME = "url-sandbox"
    DESCRIPTION = (
        "Replaces request.{func} with more secure safe_request library functions."
    )
    CHANGE_DESCRIPTION = "Switch use of requests for security.safe_requests"
    AUTHOR = "dani.alcala@pixee.ai"
    YAML_FILES = [
        "sandbox_url_creation.yaml",
    ]

    RULE_IDS = rule_ids_from_yaml_files(YAML_FILES)

    def __init__(self, context, results_by_id):
        BaseCodemod.__init__(self, results_by_id)
        BaseVisitor.__init__(self, context, self._results)

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        pos_to_match = self.get_metadata(self.METADATA_DEPENDENCIES[0], original_node)
        if self.filter_by_result(pos_to_match):
            line_number = pos_to_match.start.line
            self.CHANGES_IN_FILE.append(
                Change(str(line_number), self.CHANGE_DESCRIPTION).to_json()
            )
            AddImportsVisitor.add_needed_import(
                self.context, "security", "safe_requests"
            )
            RemoveImportsVisitor.remove_unused_import(self.context, "requests")
            return updated_node.with_changes(
                func=updated_node.func.with_changes(value=Name(replacement_import))
            )
        return updated_node
