from codemodder.codemods.test.integration_utils import BaseRemediationIntegrationTest
from core_codemods.lazy_logging import LazyLogging


class TestLazyLogging(BaseRemediationIntegrationTest):
    codemod = LazyLogging
    original_code = """
    import logging
    e = "Some error"
    logging.error("Error occurred: %s" % e)
    logging.error("Error occurred: " + e)
    """
    expected_diff_per_change = [
        '--- \n+++ \n@@ -1,4 +1,4 @@\n import logging\n e = "Some error"\n-logging.error("Error occurred: %s" % e)\n+logging.error("Error occurred: %s", e)\n logging.error("Error occurred: " + e)',
        '--- \n+++ \n@@ -1,4 +1,4 @@\n import logging\n e = "Some error"\n logging.error("Error occurred: %s" % e)\n-logging.error("Error occurred: " + e)\n+logging.error("Error occurred: %s", e)',
    ]

    expected_lines_changed = [3, 4]
    change_description = LazyLogging.change_description
    num_changes = 2
