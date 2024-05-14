from codemodder.codemods.test import BaseIntegrationTest
from codemodder.dependency import Security
from core_codemods.url_sandbox import UrlSandbox, UrlSandboxTransformer


class TestUrlSandbox(BaseIntegrationTest):
    codemod = UrlSandbox
    original_code = """
    from test_sources import untrusted_data
    import requests
    
    url = untrusted_data()
    requests.get(url)
    var = "hello"
    """
    replacement_lines = [
        (2, """from security import safe_requests\n"""),
        (5, """safe_requests.get(url)\n"""),
    ]
    expected_diff = """\
--- 
+++ 
@@ -1,6 +1,6 @@
 from test_sources import untrusted_data
-import requests
+from security import safe_requests
 
 url = untrusted_data()
-requests.get(url)
+safe_requests.get(url)
 var = "hello"
"""

    expected_line_change = "5"
    change_description = UrlSandboxTransformer.change_description
    num_changed_files = 2

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
        f"{Security.requirement}\n"
    )

    # expected because output code points to fake module
    allowed_exceptions = (ModuleNotFoundError,)
