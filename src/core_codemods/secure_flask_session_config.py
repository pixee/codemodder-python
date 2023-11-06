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

        if len(flask_visitor.config_access) == 0:
            return self.insert_config_line_endof_mod(
                tree, flask_visitor.flask_app_name, self.SECURE_SESSION_CONFIGS
            )

        # Handle single config.update line, reuse it
        if len(flask_visitor.config_access) == 1 and isinstance(
            single_config := flask_visitor.config_access[0], cst.Call
        ):
            defined_configs = self._get_configs(single_config)

            configs_to_write = {**self.SECURE_SESSION_CONFIGS.copy(), **defined_configs}

            for key, val in configs_to_write.items():
                if (
                    key in self.SECURE_SESSION_CONFIGS
                    and val in self.SECURE_SESSION_CONFIGS[key]
                ):
                    del configs_to_write[key]

            return self.reuse_config_line(
                tree, flask_visitor.flask_app_name, configs_to_write
            )

        # Handle single config['access'] line, add update line excluding configs already set
        if len(flask_visitor.config_access) == 1 and isinstance(
            single_config := flask_visitor.config_access[0], cst.Assign
        ):
            defined_config = self._get_config_from_slice(single_config)
            defined_key = list(defined_config.keys())[0]
            configs_to_write = self.SECURE_SESSION_CONFIGS.copy()

            for key, val in configs_to_write.items():
                if key in defined_config and val in self.SECURE_SESSION_CONFIGS[key]:
                    del configs_to_write[key]

            # any of the secure sesh in defined config, we want to reuse the line
            # but flip it if necessary
            if defined_key in self.SECURE_SESSION_CONFIGS:
                del configs_to_write[defined_key]
                return self.reuse_config_subscript_line(
                    tree, flask_visitor.flask_app_name, configs_to_write, defined_key
                )
            return self.insert_config_line_endof_mod(
                tree, flask_visitor.flask_app_name, configs_to_write
            )


        defined_configs = self.get_defined_configs(flask_visitor.config_access)
        breakpoint()
        configs_to_write = self.SECURE_SESSION_CONFIGS.copy()
        for key, vals in defined_configs.items():
            defined_val = vals[-1]
            if key in self.SECURE_SESSION_CONFIGS and defined_val in self.SECURE_SESSION_CONFIGS[key]:
                del configs_to_write[key]

        result = self.insert_config_line_endof_mod(
            tree, flask_visitor.flask_app_name, configs_to_write
        )
        return result

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
        # secure_configs = """SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax'"""
        final_line = cst.parse_statement(f"{app_name}.config.update({config_string})")
        new_body = original_node.body[:-1] + (final_line,)
        return original_node.with_changes(body=new_body)

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
