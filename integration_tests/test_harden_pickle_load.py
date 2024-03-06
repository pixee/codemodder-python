from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from codemodder.dependency import Fickling
from core_codemods.harden_pickle_load import HardenPickleLoad


class TestHardenPickleLoad(BaseIntegrationTest):
    codemod = HardenPickleLoad
    code_path = "tests/samples/harden_pickle.py"

    original_code, _ = original_and_expected_from_code_path(code_path, [])
    expected_new_code = """
import fickling

try:
    data = fickling.load(open("some.pickle", "rb"))
except FileNotFoundError:
    data = None
""".lstrip()

    expected_diff = """
--- 
+++ 
@@ -1,6 +1,6 @@
-import pickle
+import fickling
 
 try:
-    data = pickle.load(open("some.pickle", "rb"))
+    data = fickling.load(open("some.pickle", "rb"))
 except FileNotFoundError:
     data = None
""".lstrip()

    num_changed_files = 2
    change_description = HardenPickleLoad.change_description
    expected_line_change = 4

    requirements_path = "tests/samples/requirements.txt"
    original_requirements = "# file used to test dependency management\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n"
    expected_new_reqs = (
        "# file used to test dependency management\n"
        "requests==2.31.0\n"
        "black==23.7.*\n"
        "mypy~=1.4\n"
        "pylint>1\n"
        f"{Fickling.requirement} \\\n"
        f"{Fickling.build_hashes()}"
    )
