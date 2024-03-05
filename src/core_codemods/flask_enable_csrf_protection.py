from typing import Optional, Union

import libcst as cst

from codemodder.codemods.utils_mixin import AncestorPatternsMixin, NameResolutionMixin
from codemodder.dependency import FlaskWTF
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class FlaskEnableCSRFProtection(
    SimpleCodemod,
    NameResolutionMixin,
    AncestorPatternsMixin,
):
    metadata = Metadata(
        name="flask-enable-csrf-protection",
        summary="Enable CSRF protection globally for a Flask app.",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(url="https://owasp.org/www-community/attacks/csrf"),
            Reference(url="https://flask-wtf.readthedocs.io/en/1.2.x/csrf/"),
        ],
    )

    change_description = "Add CSRFProtect module to harden the app"

    def leave_SimpleStatementSuite(
        self,
        original_node: cst.SimpleStatementSuite,
        updated_node: cst.SimpleStatementSuite,
    ) -> cst.BaseSuite:
        if self.filter_by_path_includes_or_excludes(self.node_position(original_node)):
            new_stmts = self._get_new_stmts(original_node)
            if new_stmts:
                self.add_needed_import("flask_wtf.csrf", "CSRFProtect")
                self.add_dependency(FlaskWTF)
                self.report_change(original_node)
                return updated_node.with_changes(body=[*original_node.body, *new_stmts])
        return updated_node

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        if self.filter_by_path_includes_or_excludes(self.node_position(original_node)):
            new_stmts = self._get_new_stmts(original_node)
            if new_stmts:
                self.add_needed_import("flask_wtf.csrf", "CSRFProtect")
                self.add_dependency(FlaskWTF)
                self.report_change(original_node)
                if len(original_node.body) > 1:
                    return updated_node.with_changes(
                        body=[*original_node.body, *new_stmts]
                    )
                return cst.FlattenSentinel(
                    (updated_node, cst.SimpleStatementLine(body=[new_stmts[0]]))
                )
        return updated_node

    def _get_new_stmts(self, original_node):
        new_stmts = []
        for stmt in original_node.body:
            if maybe_small_stmt := self._handle_statement(stmt):
                new_stmts.append(maybe_small_stmt)
        return new_stmts

    def _handle_statement(self, stmt) -> Optional[cst.BaseSmallStatement]:
        match stmt:
            case cst.Assign(value=cst.Call() as call) as assign:
                base_name = self.find_base_name(call)
                if base_name and base_name == "flask.Flask":
                    named_targets = self._find_named_targets(assign)
                    flows_into_csrf_protect = map(
                        self._flows_into_csrf_protect, named_targets
                    )
                    if named_targets and not all(flows_into_csrf_protect):
                        new_stmt = cst.parse_statement(
                            f"csrf_{named_targets[0].value} = CSRFProtect({named_targets[0].value})"
                        )
                        new_stmt = cst.ensure_type(new_stmt, cst.SimpleStatementLine)
                        return new_stmt.body[0]
        return None

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
