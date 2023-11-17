from core_codemods.url_sandbox import UrlSandbox
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestUrlSandbox(BaseIntegrationTest):
    codemod = UrlSandbox
    code_path = "tests/samples/make_request.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (1, """from security import safe_requests\n"""),
            (4, """safe_requests.get(url)\n"""),
        ],
    )

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
    change_description = UrlSandbox.CHANGE_DESCRIPTION
    num_changed_files = 2

    requirements_path = "tests/samples/requirements.txt"
    original_requirements = "# file used to test dependency management\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n"
    expected_new_reqs = "# file used to test dependency management\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\nsecurity~=1.2.0\n"
