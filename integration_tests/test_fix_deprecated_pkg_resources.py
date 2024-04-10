from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.fix_deprecated_pkg_resources import FixDeprecatedPkgResources


class TestFixDeprecatedPkgResources(BaseIntegrationTest):
    codemod = FixDeprecatedPkgResources
    original_code = """
    import pkg_resources
    
    dist = pkg_resources.get_distribution("Django")
    dist.location
    version = dist.version
    """
    replacement_lines = [
        (1, "from importlib.metadata import distribution\n"),
        (3, 'dist = distribution("Django")\n'),
    ]
    expected_diff = '--- \n+++ \n@@ -1,4 +1,4 @@\n import tempfile\n \n-tempfile.mktemp()\n+tempfile.mkstemp()\n var = "hello"\n'
    expected_line_change = "3"
    change_description = FixDeprecatedPkgResources.change_description
