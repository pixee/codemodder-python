import libcst as cst
from libcst import matchers as m

from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import BaseCodemod


class FixMutableParams(BaseCodemod):
    NAME = "fix-mutable-params"
    SUMMARY = "Replace mutable parameters with None"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    DESCRIPTION = "Replace mutable parameters with None"

    _BUILTIN_TO_LITERAL = {
        "list": cst.List(elements=[]),
        "dict": cst.Dict(elements=[]),
    }

    _matches_literal: m.OneOf
    _matches_builtin: m.Call

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Looking for [], {}, or set() (which has no empty literal)
        self._matches_literal = m.OneOf(
            m.List | m.Dict | m.Set,
            m.Call(func=m.Name("set")),
        )
        # Looking for list() or dict()
        self._matches_builtin = m.Call(func=m.Name("list") | m.Name("dict"))

    def _gather_and_update_params(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ):
        updated_params = []
        new_var_decls = []

        # Iterate over all original/update parameters in parallel
        for orig, updated in zip(
            original_node.params.params,
            updated_node.params.params,
        ):
            needs_update = False
            if orig.default is not None:
                if m.matches(orig.default, self._matches_literal):
                    # We can reuse the original literal value in this case
                    new_var_decls.append(orig)
                    needs_update = True
                elif m.matches(orig.default, self._matches_builtin):
                    # Try to replace call to builtin with bare literal as long as there are no arguments
                    # Otherwise the safest thing is just to reuse the original value inline
                    new_var_decls.append(
                        orig.with_changes(
                            # Should be a safe attribute access since we've already matched the call
                            default=self._BUILTIN_TO_LITERAL[orig.default.func.value]
                        )
                        if not orig.default.args
                        else orig
                    )
                    needs_update = True

            updated_params.append(
                updated.with_changes(default=cst.Name("None")) if needs_update else orig
            )

        return updated_params, new_var_decls

    def _build_body_prefix(self, new_var_decls: list[cst.Param]):
        return [
            cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[cst.AssignTarget(target=var_decl.name)],
                        value=cst.IfExp(
                            test=cst.Comparison(
                                left=var_decl.name,
                                comparisons=[
                                    cst.ComparisonTarget(cst.Is(), cst.Name("None"))
                                ],
                            ),
                            # In the case of list() or dict(), this particular
                            # default value has been updated to use the literal
                            # instead. This does not affect the default
                            # argument in the function itself.
                            body=var_decl.default,
                            orelse=var_decl.name,
                        ),
                    )
                ]
            )
            for var_decl in new_var_decls
        ]

    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ):
        """Transforms function definitions with mutable default parameters"""
        updated_params, new_var_decls = self._gather_and_update_params(
            original_node, updated_node
        )
        # Add any new variable declarations to the top of the function body
        if body_prefix := self._build_body_prefix(new_var_decls):
            # If we're adding statements to the body, we know a change took place
            self.add_change(original_node, self.CHANGE_DESCRIPTION)

        new_body = tuple(body_prefix) + updated_node.body.body
        return updated_node.with_changes(
            params=updated_node.params.with_changes(params=updated_params),
            body=updated_node.body.with_changes(body=new_body),
        )
