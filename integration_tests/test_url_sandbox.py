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
            (0, """from security import safe_requests\n"""),
            (2, """safe_requests.get("www.google.com")\n"""),
        ],
    )

    expected_diff = '--- \n+++ \n@@ -1,4 +1,4 @@\n-import requests\n+from security import safe_requests\n \n-requests.get("www.google.com")\n+safe_requests.get("www.google.com")\n var = "hello"\n'
    expected_line_change = "3"
    change_description = UrlSandbox.CHANGE_DESCRIPTION
    num_changed_files = 2

    requirements_path = "tests/samples/requirements.txt"
    original_requirements = "# file used to test dependency management\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n"
    expected_new_reqs = (
        "requests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\nsecurity==1.0.1"
    )
