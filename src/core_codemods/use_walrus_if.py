from typing import List, Tuple, Optional

import libcst as cst
from libcst._position import CodeRange
from libcst import matchers as m
from libcst.metadata import ParentNodeProvider, ScopeProvider

from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class UseWalrusIf(SemgrepCodemod):
    METADATA_DEPENDENCIES = SemgrepCodemod.METADATA_DEPENDENCIES + (
        ParentNodeProvider,
        ScopeProvider,
    )
    NAME = "use-walrus-if"
    SUMMARY = "Use Assignment Expression (Walrus) In Conditional"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    DESCRIPTION = (
        "Replaces multiple expressions involving `if` operator with 'walrus' operator."
    )
    REFERENCES = [
        {
            "url": "https://docs.python.org/3/whatsnew/3.8.html#assignment-expressions",
            "description": "",
        }
    ]

    @classmethod
    def rule(cls):
        return """
        rules:
          - patterns:
            - pattern: |
                $ASSIGN
                if $COND:
                  $BODY
            - metavariable-pattern:
                metavariable: $ASSIGN
                patterns:
                  - pattern: $VAR = $RHS
                  - metavariable-pattern:
                      metavariable: $COND
                      patterns:
                        - pattern: $VAR
                  - metavariable-pattern:
                      metavariable: $BODY
                      pattern: $VAR
            - focus-metavariable: $ASSIGN
        """

    _modify_next_if: List[Tuple[CodeRange, cst.Assign]]
    _if_stack: List[Optional[Tuple[CodeRange, cst.Assign]]]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._modify_next_if = []
        self._if_stack = []

    def visit_If(self, node):
        self._if_stack.append(
            self._modify_next_if.pop() if len(self._modify_next_if) else None
        )

    def leave_If(self, original_node, updated_node):
        if (result := self._if_stack.pop()) is not None:
            position, if_node = result
            is_name = m.matches(updated_node.test, m.Name())
            named_expr = cst.NamedExpr(
                target=if_node.targets[0].target,
                value=if_node.value,
                lpar=[] if is_name else [cst.LeftParen()],
                rpar=[] if is_name else [cst.RightParen()],
            )
            self.add_change_from_position(position, self.CHANGE_DESCRIPTION)
            return (
                updated_node.with_changes(test=named_expr)
                if is_name
                else updated_node.with_changes(
                    test=updated_node.test.with_changes(left=named_expr)
                )
            )

        return original_node

    def _is_valid_modification(self, node):
        """
        Restricts the kind of modifications we can make to the AST.

        This is necessary since the semgrep rule can't fully encode this restriction.
        """
        if parent := self.get_metadata(ParentNodeProvider, node):
            if gparent := self.get_metadata(ParentNodeProvider, parent):
                if (idx := gparent.children.index(parent)) >= 0:
                    return m.matches(
                        gparent.children[idx + 1],
                        m.If(test=(m.Name() | m.Comparison(left=m.Name()))),
                    )
        return False

    def leave_Assign(self, original_node, updated_node):
        if self.node_is_selected(original_node):
            if self._is_valid_modification(original_node):
                position = self.node_position(original_node)
                self._modify_next_if.append((position, updated_node))
                return cst.RemoveFromParent()

        return original_node

    def leave_SimpleStatementLine(self, original_node, updated_node):
        """
        Preserves the whitespace and comments in the line when all children are removed.

        This feels like a bug in libCST but we'll work around it for now.
        """
        if not updated_node.body:
            trailing_whitespace = (
                (
                    original_node.trailing_whitespace.with_changes(
                        whitespace=cst.SimpleWhitespace(""),
                    ),
                )
                if original_node.trailing_whitespace.comment
                else ()
            )
            # NOTE: The effect of this is to preserve the
            # whitespace and comments. However, the type expected by
            # cst.Module.body is Sequence[Union[SimpleStatementLine, BaseCompoundStatement]].
            # So technically this violates the expected return type since we
            # are not adding a new SimpleStatementLine but instead just bare
            # EmptyLine and Comment nodes.
            # A more correct solution would involve transferring any whitespace
            # and comments to the subsequent SimpleStatementLine (which
            # contains the If statement), but this would require a lot more
            # state management to fit within the visitor pattern. We should
            # revisit this at some point later.
            return cst.FlattenSentinel(
                original_node.leading_lines + trailing_whitespace
            )

        return updated_node
