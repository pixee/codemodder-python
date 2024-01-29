from core_codemods.lazy_logging import LazyLogging
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestLazyLogging(BaseIntegrationTest):
    codemod = LazyLogging
    code_path = "tests/samples/lazy_logging.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (2, """logging.error("Error occurred: %s", e)\n"""),
            (3, """logging.error("Error occurred: %s", e)\n"""),
        ],
    )

    # fmt: off
    expected_diff =(
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
