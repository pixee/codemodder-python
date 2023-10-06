from core_codemods.with_threading_lock import WithThreadingLock
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestWithThreadingLock(BaseIntegrationTest):
    codemod = WithThreadingLock
    code_path = "tests/samples/with_threading_lock.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (1, "lock = threading.Lock()\n"),
            (2, "with lock:\n"),
            (4, '    print("Hello")\n'),
        ],
    )
    expected_diff = '--- \n+++ \n@@ -1,3 +1,4 @@\n import threading\n-with threading.Lock():\n+lock = threading.Lock()\n+with lock:\n     print("Hello")\n'
    expected_line_change = "2"
    change_description = WithThreadingLock.CHANGE_DESCRIPTION
