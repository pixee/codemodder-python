from typing import Union
import libcst as cst
from codemodder.codemods.api import BaseCodemod
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.utils_mixin import AncestorPatternsMixin, NameResolutionMixin
from codemodder.dependency import FLaskWTF


class FlaskEnableCSRFProtection(
    BaseCodemod, NameResolutionMixin, AncestorPatternsMixin
):
    NAME = "flask-enable-csrf-protection"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    DESCRIPTION = "Uses CSRFProtect module to harden the app."
    SUMMARY = "Enable CSRF protection globally for a Flask app."
    REFERENCES = [
        {"url": "https://owasp.org/www-community/attacks/csrf", "description": ""},
    ]

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        if self.filter_by_path_includes_or_excludes(self.node_position(original_node)):
            match original_node.body:
                case [cst.Assign(value=cst.Call() as call) as assign]:
                    base_name = self.find_base_name(call)
                    if base_name and base_name == "flask.Flask":
                        named_targets = self._find_named_targets(assign)
                        flows_into_csrf_protect = map(
                            self._flows_into_csrf_protect, named_targets
                        )
                        if named_targets and not all(flows_into_csrf_protect):
                            self.add_needed_import("flask_wtf.csrf", "CSRFProtect")
                            self.add_dependency(FLaskWTF)
                            self.report_change(original_node)
                            return cst.FlattenSentinel(
                                [
                                    updated_node,
                                    cst.parse_statement(
                                        f"csrf = CSRFProtect({named_targets[0].value})"
                                    ),
                                ]
                            )
        return updated_node

    def _find_named_targets(self, node: cst.Assign) -> list[cst.Name]:
        all_names = []
        for at in node.targets:
            match at:
                case cst.AssignTarget(target=cst.Name() as target):
                    all_names.append(target)
        return all_names

    def _flows_into_csrf_protect(self, name: cst.Name) -> bool:
        accesses = self.find_accesses(name)
        for access in accesses:
            maybe_arg = self.is_argument_of_call(access.node)
            maybe_call = self.get_parent(maybe_arg) if maybe_arg else None
            if (
                maybe_call
                and self.find_base_name(maybe_call) == "flask_wtf.csrf.CSRFProtect"
            ):
                return True
        return False
