from codemodder.codemods.url_sandbox import UrlSandbox
from integration_tests.base_test import BaseIntegrationTest


class TestUrlSandbox(BaseIntegrationTest):
    codemod = UrlSandbox
    codemod_name = UrlSandbox.NAME
    code_path = "tests/samples/make_request.py"
    original_code = 'import requests\n\nrequests.get("www.google.com")\nvar = "hello"\n'
    expected_new_code = 'from security import safe_requests\n\nsafe_requests.get("www.google.com")\nvar = "hello"\n'
