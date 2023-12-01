from core_codemods.numpy_nan_equality import NumpyNanEquality
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestNumpyNanEquality(BaseIntegrationTest):
    codemod = NumpyNanEquality
    code_path = "tests/samples/numpy_nan_equality.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (3, """if np.isnan(a):\n"""),
        ],
    )

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -1,5 +1,5 @@\n"""
    """ import numpy as np\n"""
    """ \n"""
    """ a = np.nan\n"""
    """-if a == np.nan:\n"""
    """+if np.isnan(a):\n"""
    """     pass\n"""
    )
    # fmt: on

    expected_line_change = "4"
    change_description = NumpyNanEquality.CHANGE_DESCRIPTION
    num_changed_files = 1
