from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.fix_deprecated_logging_warn import FixDeprecatedLoggingWarn


class TestFixDeprecatedLoggingWarn(BaseIntegrationTest):
    codemod = FixDeprecatedLoggingWarn
    original_code = """
    import logging

    log = logging.getLogger("my logger")
    log.warn("hello")
    """
    replacement_lines = [(4, 'log.warning("hello")\n')]
    expected_diff = '--- \n+++ \n@@ -1,4 +1,4 @@\n import logging\n \n log = logging.getLogger("my logger")\n-log.warn("hello")\n+log.warning("hello")\n'
    expected_line_change = "4"
    change_description = FixDeprecatedLoggingWarn.change_description
