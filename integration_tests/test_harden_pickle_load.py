from codemodder.codemods.test import BaseIntegrationTest
from codemodder.dependency import Fickling
from core_codemods.harden_pickle_load import HardenPickleLoad


class TestHardenPickleLoad(BaseIntegrationTest):
    codemod = HardenPickleLoad
    original_code = """
    import pickle
    
    try:
        data = pickle.load(open("some.pickle", "rb"))
    except FileNotFoundError:
        data = None
    """
    expected_new_code = """
    import fickling
    
    try:
        data = fickling.load(open("some.pickle", "rb"))
    except FileNotFoundError:
        data = None
    """

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
     data = None""".lstrip()

    num_changed_files = 2
    change_description = HardenPickleLoad.change_description
    expected_line_change = 4

    requirements_file_name = "requirements.txt"
    original_requirements = (
        "# file used to test dependency management\n"
        "requests==2.31.0\n"
        "black==23.7.*\n"
        "mypy~=1.4\n"
        "pylint>1\n"
    )
    expected_requirements = (
        "# file used to test dependency management\n"
        "requests==2.31.0\n"
        "black==23.7.*\n"
        "mypy~=1.4\n"
        "pylint>1\n"
        f"{Fickling.requirement}\n"
    )
