from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.numpy_nan_equality import NumpyNanEqualityTransformer
from core_codemods.sonar.sonar_numpy_nan_equality import SonarNumpyNanEquality


class TestNumpyNanEquality(SonarIntegrationTest):
    codemod = SonarNumpyNanEquality
    code_path = "tests/samples/numpy_nan_equality.py"
    replacement_lines = [
        (4, """if np.isnan(a):\n"""),
    ]

    # fmt: off
    expected_diff = (
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
    change_description = NumpyNanEqualityTransformer.change_description
    num_changed_files = 1
