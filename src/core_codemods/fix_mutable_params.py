import libcst as cst
from libcst import matchers as m

from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import BaseCodemod


class FixMutableParams(BaseCodemod):
    NAME = "fix-mutable-params"
    SUMMARY = "Replace Mutable Default Parameters"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Replace mutable parameter with `None`."
    REFERENCES: list = []
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

    def _create_annotation(self, orig: cst.Param, updated: cst.Param):
        match orig.annotation:
            case cst.Annotation(annotation=cst.Subscript(sub)):
                match sub:  # type: ignore
                    case cst.Name("Optional"):
                        # Already an Optional, so we can just preserve the original annotation
                        return updated.annotation

        return (
            updated.annotation.with_changes(
                annotation=cst.Subscript(
                    value=cst.Name("Optional"),
                    slice=[
                        cst.SubscriptElement(
                            slice=cst.Index(value=updated.annotation.annotation)
                        )
                    ],
                )
            )
            if orig.annotation is not None and updated.annotation is not None
            else None
        )

    def _gather_and_update_params(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ):
        updated_params = []
        new_var_decls = []
        add_annotation = False

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

            annotation = (
                self._create_annotation(orig, updated) if needs_update else None
            )
            add_annotation = add_annotation or annotation is not None
            updated_params.append(
                updated.with_changes(
                    default=cst.Name("None"),
                    annotation=annotation,
                )
                if needs_update
                else updated,
            )

        return updated_params, new_var_decls, add_annotation

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

    def _build_new_body(self, new_var_decls, body):
        offset = 0
        new_body = []

        # Preserve placement of docstring
        if body and m.matches(
            body[0],
            m.SimpleStatementLine(body=[m.Expr(value=m.SimpleString())]),
        ):
            new_body.append(body[0])
            offset = 1

        new_body.extend(self._build_body_prefix(new_var_decls))
        new_body.extend(body[offset:])
        return new_body

    def _is_abstractmethod(self, node: cst.FunctionDef) -> bool:
        for decorator in node.decorators:
            match decorator.decorator:
                case cst.Name("abstractmethod"):
                    return True

        return False

    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ):
        """Transforms function definitions with mutable default parameters"""
        # TODO: add filter by include or exclude that works for nodes
        # that that have different start/end numbers.
        (
            updated_params,
            new_var_decls,
            add_annotation,
        ) = self._gather_and_update_params(original_node, updated_node)
        new_body = (
            self._build_new_body(new_var_decls, updated_node.body.body)
            if not self._is_abstractmethod(original_node)
            else updated_node.body.body
        )
        if new_var_decls:
            # If we're adding statements to the body, we know a change took place
            self.add_change(original_node, self.CHANGE_DESCRIPTION)
        if add_annotation:
            self.add_needed_import("typing", "Optional")

        return updated_node.with_changes(
            params=updated_node.params.with_changes(params=updated_params),
            body=updated_node.body.with_changes(body=new_body),
        )
