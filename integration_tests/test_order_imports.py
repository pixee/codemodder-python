from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.order_imports import OrderImports


class TestOrderImports(BaseIntegrationTest):
    codemod = OrderImports
    original_code = """
    #!/bin/env python
    from abc import ABCMeta
    
    # comment builtins1
    # comment builtins2
    import builtins
    
    # comment a
    from abc import ABC
    
    # comment builtins3
    import builtins, datetime
    
    # comment builtins4
    # comment builtins5
    import builtins
    import collections
    
    ABC
    ABCMeta
    builtins
    collections
    datetime
    """
    expected_new_code = """
    #!/bin/env python
    # comment builtins4
    # comment builtins5
    # comment builtins3
    # comment builtins1
    # comment builtins2
    import builtins
    import collections
    import datetime
    # comment a
    from abc import ABC, ABCMeta
    
    ABC
    ABCMeta
    builtins
    collections
    datetime
    """
    expected_diff = "--- \n+++ \n@@ -1,20 +1,14 @@\n #!/bin/env python\n-from abc import ABCMeta\n-\n+# comment builtins4\n+# comment builtins5\n+# comment builtins3\n # comment builtins1\n # comment builtins2\n import builtins\n-\n+import collections\n+import datetime\n # comment a\n-from abc import ABC\n-\n-# comment builtins3\n-import builtins, datetime\n-\n-# comment builtins4\n-# comment builtins5\n-import builtins\n-import collections\n+from abc import ABC, ABCMeta\n \n ABC\n ABCMeta\n"
    expected_line_change = "2"
    change_description = OrderImports.change_description
