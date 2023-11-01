import libcst as cst
from libcst.codemod import Codemod, CodemodContext, ContextAwareVisitor
from libcst.metadata import ParentNodeProvider, ScopeProvider

from libcst import matchers
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import BaseCodemod
from codemodder.codemods.utils_mixin import NameResolutionMixin


class SecureFlaskSessionConfig(BaseCodemod):
    METADATA_DEPENDENCIES = BaseCodemod.METADATA_DEPENDENCIES + (
        ParentNodeProvider,
        ScopeProvider,
    )
    NAME = "secure-flask-session-configuration"
    SUMMARY = "UTODO"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_REVIEW
    DESCRIPTION = "TODO"
    REFERENCES = [
        {
            "url": "todo",
            "description": "",
        }
    ]

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        flask_visitor = FindConfigCalls(self.context)
        tree.visit(flask_visitor)
        if not flask_visitor.flask_app_name:
            return tree

        # TODO: iterate through flask_visitor.config_access
        # TODO: use a list of secure config names, values to only write the needed ones out
        result = self.insert_config_line_endof_mod(tree, flask_visitor.flask_app_name)
        return result

    def insert_config_line_endof_mod(
        self, original_node: cst.Module, app_name: str
    ) -> cst.Module:
        # TODO: record change
        # line_number is the end of the module where we will insert the new flag.
        # pos_to_match = self.node_position(original_node)
        # line_number = pos_to_match.end.line
        # self.changes_in_file.append(
        #     Change(line_number, DjangoSessionCookieSecureOff.CHANGE_DESCRIPTION)
        # )
        # self.file_context.codemod_changes.append(
        #     Change(line_number, self.CHANGE_DESCRIPTION)
        # )
        secure_configs = """SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax'"""
        final_line = cst.parse_statement(f"{app_name}.config.update({secure_configs})")
        new_body = original_node.body + (final_line,)
        return original_node.with_changes(body=new_body)


class FindConfigCalls(ContextAwareVisitor, NameResolutionMixin):
    """
    Visitor to find calls to flask.Flask and related `.config` accesses.
    """

    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def __init__(self, context: CodemodContext) -> None:
        self.config_access: list = []
        self.flask_app_name = ""
        super().__init__(context)

    def _find_config_accesses(self, flask_app_attr: cst.AnnAssign | cst.Assign):
        assignments = self.find_assignments(flask_app_attr)
        for assignment in assignments:
            if assignment.references:
                # Flask app instance is accessed
                references_to_app = [x.node for x in assignment.references]
                for node in references_to_app:
                    parent = self.get_metadata(ParentNodeProvider, node)
                    match parent:
                        case cst.Attribute():
                            config = cst.Name(value="config")
                            if matchers.matches(
                                parent, matchers.Attribute(value=node, attr=config)
                            ):
                                gparent = self.get_metadata(ParentNodeProvider, parent)
                                self.config_access.append(gparent)

    def leave_Call(self, original_node: cst.Call) -> None:
        true_name = self.find_base_name(original_node.func)
        if true_name == "flask.Flask":
            flask_app_parent = self.get_metadata(ParentNodeProvider, original_node)
            match flask_app_parent:
                case cst.AnnAssign() | cst.Assign():
                    flask_app_attr = flask_app_parent.targets[0].target
                    self.flask_app_name = flask_app_attr.value
                    self._find_config_accesses(flask_app_attr)

        return original_node
