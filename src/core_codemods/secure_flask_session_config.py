import libcst as cst
from libcst import matchers
from libcst.codemod import Codemod, CodemodContext
from libcst.metadata import ParentNodeProvider

from codemodder.codemods.base_visitor import BaseTransformer
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.codetf import Change
from codemodder.file_context import FileContext
from codemodder.utils.utils import extract_targets_of_assignment, true_value
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class SecureFlaskSessionConfig(SimpleCodemod, Codemod):
    metadata = Metadata(
        name="secure-flask-session-configuration",
        summary="Flip Insecure `Flask` Session Configurations",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(
                url="https://owasp.org/www-community/controls/SecureCookieAttribute"
            ),
            Reference(
                url="https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html"
            ),
        ],
    )
    change_description = "Flip Flask session configuration if defined as insecure."

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        flask_codemod = FixFlaskConfig(self.context, self.file_context)
        result_tree = flask_codemod.transform_module(tree)

        if not flask_codemod.flask_app_name:
            return tree

        # Later: if we want to write at the end of the module any
        # default insecure configs.
        # if flask_codemod.configs_to_write:
        #     return self.insert_secure_configs(
        #         tree,
        #         result_tree,
        #         flask_codemod.flask_app_name,
        #         flask_codemod.configs_to_write,
        #     )
        return result_tree

    # def insert_secure_configs(
    #     self,
    #     original_node: cst.Module,
    #     updated_node: cst.Module,
    #     app_name: str,
    #     configs: dict,
    # ) -> cst.Module:
    #     if not configs:
    #         return updated_node
    #
    #     config_string = ", ".join(
    #         f"{key}='{value[0]}'" if isinstance(value[0], str) else f"{key}={value[0]}"
    #         for key, value in configs.items()
    #         if value and value[0] is not None
    #     )
    #     if not config_string:
    #         return updated_node
    #
    #     self.report_change_endof_module(original_node)
    #     final_line = cst.parse_statement(f"{app_name}.config.update({config_string})")
    #     new_body = updated_node.body + (final_line,)
    #     return updated_node.with_changes(body=new_body)
    #
    # def report_change_endof_module(self, original_node: cst.Module) -> None:
    #     # line_number is the end of the module where we will insert the new line.
    #     pos_to_match = self.node_position(original_node)
    #     line_number = pos_to_match.end.line
    #     self.file_context.codemod_changes.append(
    #         Change(line_number, self.CHANGE_DESCRIPTION)
    #     )


class FixFlaskConfig(BaseTransformer, NameResolutionMixin):
    """
    Visitor to find calls to flask.Flask and related `.config` accesses.
    """

    METADATA_DEPENDENCIES = (
        *BaseTransformer.METADATA_DEPENDENCIES,
        ParentNodeProvider,
    )
    SECURE_SESSION_CONFIGS = {
        # None value indicates unassigned, using default is safe
        # values in order of precedence
        "SESSION_COOKIE_HTTPONLY": [None, True],
        "SESSION_COOKIE_SECURE": [True],
        "SESSION_COOKIE_SAMESITE": ["Lax", "Strict"],
    }

    def __init__(self, codemod_context: CodemodContext, file_context: FileContext):
        super().__init__(
            codemod_context, [], file_context.line_include, file_context.line_exclude
        )
        self.flask_app_name = ""
        # Later: if we want to store configs to write later
        # self.configs_to_write = self.SECURE_SESSION_CONFIGS.copy()
        self.file_context = file_context

    def _store_flask_app(self, original_node) -> None:
        flask_app_parent = self.get_metadata(ParentNodeProvider, original_node)
        match flask_app_parent:
            case cst.AnnAssign() | cst.Assign():
                targets = extract_targets_of_assignment(flask_app_parent)
                # TODO: handle other assignments ex. l[0] = Flask(...) , a.b = Flask(...)
                if targets and matchers.matches(
                    first_target := targets[0], matchers.Name()
                ):
                    self.flask_app_name = first_target.value

    # def _remove_config(self, key):
    #     try:
    #         del self.configs_to_write[key]
    #     except KeyError:
    #         pass

    def _get_secure_config_val(self, key):
        val = self.SECURE_SESSION_CONFIGS[key][0] or self.SECURE_SESSION_CONFIGS[key][1]
        return cst.parse_expression(f'"{val}"' if isinstance(val, str) else f"{val}")

    @property
    def flask_app_is_assigned(self):
        return bool(self.flask_app_name)

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        if self.find_base_name(original_node.func) == "flask.Flask":
            self._store_flask_app(original_node)

        if self.flask_app_is_assigned and self._is_config_update_call(original_node):
            return self.call_node_with_secure_configs(original_node, updated_node)
        return updated_node

    def call_node_with_secure_configs(
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.Call:
        new_args = []
        changed = False
        for arg in updated_node.args:
            if (
                arg.keyword
                and (key := arg.keyword.value) in self.SECURE_SESSION_CONFIGS
            ):
                # self._remove_config(key)
                if true_value(arg.value) not in self.SECURE_SESSION_CONFIGS[key]:  # type: ignore
                    safe_value = self._get_secure_config_val(key)
                    arg = arg.with_changes(value=safe_value)
                    changed = True
            new_args.append(arg)

        if changed:
            self.report_change(original_node)
        return updated_node.with_changes(args=new_args)

    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign):
        if self.flask_app_is_assigned and self._is_config_subscript(original_node):
            return self.assign_node_with_secure_config(original_node, updated_node)
        return updated_node

    def assign_node_with_secure_config(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.Assign:
        key = true_value(updated_node.targets[0].target.slice[0].slice.value)
        if key in self.SECURE_SESSION_CONFIGS:
            # self._remove_config(key)
            if true_value(updated_node.value) not in self.SECURE_SESSION_CONFIGS[key]:  # type: ignore
                safe_value = self._get_secure_config_val(key)
                self.report_change(original_node)
                return updated_node.with_changes(value=safe_value)
        return updated_node

    def _is_config_update_call(self, original_node: cst.Call):
        config = matchers.Name(value="config")
        app_name = matchers.Name(value=self.flask_app_name)
        app_config_node = matchers.Attribute(value=app_name, attr=config)
        update = cst.Name(value="update")
        return matchers.matches(
            original_node.func, matchers.Attribute(value=app_config_node, attr=update)
        )

    def _is_config_subscript(self, original_node: cst.Assign):
        config = matchers.Name(value="config")
        app_name = matchers.Name(value=self.flask_app_name)
        app_config_node = matchers.Attribute(value=app_name, attr=config)
        return matchers.matches(
            original_node.targets[0].target, matchers.Subscript(value=app_config_node)
        )

    def report_change(self, original_node):
        line_number = self.lineno_for_node(original_node)
        self.file_context.codemod_changes.append(
            Change(
                lineNumber=line_number,
                description=SecureFlaskSessionConfig.change_description,
            )
        )
