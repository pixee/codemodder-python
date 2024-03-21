from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.with_threading_lock import WithThreadingLock


class TestWithThreadingLock(BaseIntegrationTest):
    codemod = WithThreadingLock
    original_code = """
    import threading
    with threading.Lock():
        print("Hello")
    """
    replacement_lines = [
        (2, "lock = threading.Lock()\n"),
        (3, "with lock:\n"),
        (5, '    print("Hello")\n'),
    ]

    expected_diff = '--- \n+++ \n@@ -1,3 +1,4 @@\n import threading\n-with threading.Lock():\n+lock = threading.Lock()\n+with lock:\n     print("Hello")\n'
    expected_line_change = "2"
    change_description = WithThreadingLock.change_description
