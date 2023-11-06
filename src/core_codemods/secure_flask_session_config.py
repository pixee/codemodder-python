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

    SECURE_SESSION_CONFIGS = dict(
        # None value indicates unassigned, using default is safe
        # values in order of precedence
        SESSION_COOKIE_HTTPONLY=[None, True],
        SESSION_COOKIE_SECURE=[True],
        SESSION_COOKIE_SAMESITE=["Lax", "Strict"],
    )

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        flask_visitor = FindConfigCalls(self.context)
        tree.visit(flask_visitor)
        if not flask_visitor.flask_app_name:
            return tree

        if len(config_access := flask_visitor.config_access) == 0:
            return self.insert_config_line_endof_mod(
                tree, flask_visitor.flask_app_name, self.SECURE_SESSION_CONFIGS
            )

        configs_to_write = self.SECURE_SESSION_CONFIGS.copy()

        for config_line in config_access:
            match config_line:
                case cst.Call():
                    # app.config.update(...)
                    # defined_configs = self._get_configs(config_line)
                    for arg in config_line.args:
                        key = arg.keyword.value
                        val = [true_value(arg.value)]
                        if key in self.SECURE_SESSION_CONFIGS and val not in self.SECURE_SESSION_CONFIGS[key]:
                            del configs_to_write[key]
                            secure_val = self.SECURE_SESSION_CONFIGS[key][0]
                            arg.with_changes(value=cst.parse_expression(f"{secure_val}"))

                case cst.Assign():
                    # app.config['...']
                    defined_config = self._get_config_from_slice(config_line)

                    (key, vals), = defined_config.items()

                    defined_val = true_value(vals[-1])
                    if key in self.SECURE_SESSION_CONFIGS and defined_val not in self.SECURE_SESSION_CONFIGS[key]:
                        del configs_to_write[key]
                        secure_val = self.SECURE_SESSION_CONFIGS[key][0]
                        config_line.with_changes(value=cst.parse_expression(f"{secure_val}"))

        if isinstance(config_update := config_access[-1], cst.Call):
            # If the last config access is of form `app.config.update...`
            # reuse that line.
            self.reuse_config_line(config_update, configs_to_write)
            return tree
        # todo: if there is an .update line, add values directly there
        return self.insert_config_line_endof_mod(
            tree, flask_visitor.flask_app_name, configs_to_write
        )

    def get_defined_configs(self, config_access):
        all_defined_configs = {}
        for config_line in config_access:
            match config_line:
                case cst.Call():
                    # app.config.update(...)
                    defined_configs = self._get_configs(config_line)
                    all_defined_configs.update(defined_configs)
                case cst.Assign():
                    # app.config['...']
                    defined_configs = self._get_config_from_slice(config_line)
                    all_defined_configs.update(defined_configs)

        return all_defined_configs
    def _get_configs(self, config_line: cst.Call):
        defined_configs = {}
        for arg in config_line.args:
            defined_configs[arg.keyword.value] = [true_value(arg.value)]
        return defined_configs

    def _get_config_from_slice(self, config_line: cst.Assign):
        defined_configs = {}
        key = true_value(config_line.targets[0].target.slice[0].slice.value)
        defined_configs[key] = [true_value(config_line.value)]
        return defined_configs

    def reuse_config_line(
        self, config_line: cst.Call,  configs: dict
    ) -> None:
        if not configs:
            return
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
        # config_string = ", ".join(
        #     f"{key}='{value[0]}'" if isinstance(value[0], str) else f"{key}={value[0]}"
        #     for key, value in configs.items()
        #     if value and value[0] is not None
        # )
        # final_line = cst.parse_statement(f"{app_name}.config.update({config_string})")
        # new_body = original_node.body[:-1] + (final_line,)
        from codemodder.codemods.api.helpers import NewArg

        to_add = [NewArg(name=key, value=str(vals[0]), add_if_missing=True) for key, vals in configs.items() if vals[0] is not None]

        new_args = self.replace_args(
            config_line, to_add
        )
        # self.update_arg_target(config_line, new_args)
        config_line.with_changes(args=new_args)

    def reuse_config_subscript_line(
        self, original_node: cst.Module, app_name: str, configs: dict, defined_key: str
    ) -> cst.Module:
        if not configs:
            return original_node
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
        config_string = ", ".join(
            f"{key}='{value[0]}'" if isinstance(value[0], str) else f"{key}={value[0]}"
            for key, value in configs.items()
            if value and value[0] is not None
        )

        final_line = cst.parse_statement(f"{app_name}.config.update({config_string})")
        secure_val = (
            self.SECURE_SESSION_CONFIGS[defined_key][0]
            or self.SECURE_SESSION_CONFIGS[defined_key][1]
        )
        final_config_subscript_line = cst.parse_statement(
            f"{app_name}.config['{defined_key}'] = {secure_val}"
        )
        new_body = original_node.body[:-1] + (
            final_config_subscript_line,
            final_line,
        )
        return original_node.with_changes(body=new_body)

    def insert_config_line_endof_mod(
        self, original_node: cst.Module, app_name: str, configs: dict
    ) -> cst.Module:
        if not configs:
            return original_node
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
        config_string = ", ".join(
            f"{key}='{value[0]}'" if isinstance(value[0], str) else f"{key}={value[0]}"
            for key, value in configs.items()
            if value and value[0] is not None
        )
        if not config_string:
            return original_node
        final_line = cst.parse_statement(f"{app_name}.config.update({config_string})")
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
                                ggparent = self.get_metadata(
                                    ParentNodeProvider, gparent
                                )
                                if matchers.matches(gparent, matchers.Subscript()):
                                    gggparent = self.get_metadata(
                                        ParentNodeProvider, ggparent
                                    )
                                    self.config_access.append(gggparent)
                                else:
                                    self.config_access.append(ggparent)

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


def true_value(node: cst.Name | cst.SimpleString):
    # todo: move to a more general util
    from codemodder.project_analysis.file_parsers.utils import clean_simplestring

    # convert 'True' to True, etc
    # '123'  to 123
    # leave strs as they are
    # Try to convert the string to a boolean, integer, or float
    match node:
        case cst.SimpleString():
            return clean_simplestring(node)
        case cst.Name():
            val = node.value
            if val.lower() == "true":
                return True
            elif val.lower() == "false":
                return False
            try:
                return int(val)
            except ValueError:
                try:
                    return float(val)
                except ValueError:
                    # If no conversion worked, return the original string
                    return val
