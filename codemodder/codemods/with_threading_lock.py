import libcst as cst
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class WithThreadingLock(SemgrepCodemod):
    NAME = "bad-lock-with-statement"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    DESCRIPTION = "Separates threading lock instantiation and call with `with` statement into two steps."

    @classmethod
    def rule(cls):
        return """
        rules:
          - id: bad-lock-with-statement
            pattern-either:
              - patterns:
                - pattern: |
                    with threading.Lock():
                        ...
                - pattern-inside: |
                    import threading
                    ...
        """

    # def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
    #     # collides with WithItem
    #     return original_node
    def on_result_found(self, _, updated_node):
        breakpoint()
        # new_with_stmt = cst.parse_module("lock")

        # second = cst.parse_expressionZ("with lock:")
        # breakpoint()
        # new_item = cst.Call(func=cst.Attribute(value=cst.parse_expression("requirement"), attr=cst.Name("idk")))

        # code that works in leave_With
        # first = cst.parse_statement("lock = threading.Lock()")
        # new_item = cst.Name(value="lock")
        # new_node = updated_node.with_changes(items=(cst.WithItem(new_item), ))
        # return cst.FlattenSentinel([first, new_node])
        ###

        # code for Leave_WithItem
        return cst.FlattenSentinel([updated_node, updated_node])

        # second = updated_node.with_changes(items=(updated_node.items[0].with_changes(item=new_item,)))

        # cst.WithItem(cst.Name(value="lock"))])
