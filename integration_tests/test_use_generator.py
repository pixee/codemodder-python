from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.use_generator import UseGenerator


class TestUseGenerator(BaseIntegrationTest):
    codemod = UseGenerator
    original_code = """
    def some(iterable):
        for i in iterable:
            yield i


    x = sum([i for i in range(1000)])
    y = some([i for i in range(1000)])
    """
    replacement_lines = [(6, "x = sum(i for i in range(1000))\n")]

    expected_diff = """\
--- 
+++ 
@@ -3,5 +3,5 @@
         yield i
 
 
-x = sum([i for i in range(1000)])
+x = sum(i for i in range(1000))
 y = some([i for i in range(1000)])
"""

    expected_line_change = "6"
    change_description = UseGenerator.change_description
