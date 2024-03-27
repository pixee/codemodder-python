from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.lazy_logging import LazyLogging


class TestLazyLogging(BaseIntegrationTest):
    codemod = LazyLogging
    original_code = """
    import logging
    e = "Some error"
    logging.error("Error occurred: %s" % e)
    logging.error("Error occurred: " + e)
    """
    replacement_lines = [
        (3, """logging.error("Error occurred: %s", e)\n"""),
        (4, """logging.error("Error occurred: %s", e)\n"""),
    ]
    # fmt: off
    expected_diff = (
    """--- \n"""
    """+++ \n"""
    """@@ -1,4 +1,4 @@\n"""
    """ import logging\n"""
    """ e = "Some error"\n"""
    """-logging.error("Error occurred: %s" % e)\n"""
    """-logging.error("Error occurred: " + e)\n"""
    """+logging.error("Error occurred: %s", e)\n"""
    """+logging.error("Error occurred: %s", e)\n""")
    # fmt: on

    expected_line_change = "3"
    change_description = LazyLogging.change_description
    num_changes = 2
