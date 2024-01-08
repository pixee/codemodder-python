from core_codemods.fix_deprecated_logging_warn import FixDeprecatedLoggingWarn
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestFixDeprecatedLoggingWarn(BaseIntegrationTest):
    codemod = FixDeprecatedLoggingWarn
    code_path = "tests/samples/fix_deprecated_logging_warn.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path, [(3, 'log.warning("hello")\n')]
    )
    expected_diff = '--- \n+++ \n@@ -1,4 +1,4 @@\n import logging\n \n log = logging.getLogger("my logger")\n-log.warn("hello")\n+log.warning("hello")\n'
    expected_line_change = "4"
    change_description = FixDeprecatedLoggingWarn.CHANGE_DESCRIPTION
