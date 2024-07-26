from functools import cached_property

from codemodder.codemods.import_modifier_codemod import SecurityImportModifierCodemod
from codemodder.codemods.libcst_transformer import LibcstTransformerPipeline
from codemodder.codemods.semgrep import SemgrepRuleDetector
from codemodder.dependency import Dependency, Security
from core_codemods.api import CoreCodemod, Metadata, Reference, ReviewGuidance


class UrlSandboxTransformer(SecurityImportModifierCodemod):
    change_description = "Switch use of requests for security.safe_requests"

    @cached_property
    def mapping(self) -> dict[str, str]:
        """Build a mapping of functions to their safe_requests imports"""
        _matching_functions: dict[str, str] = {
            "requests.get": "safe_requests",
        }
        return _matching_functions

    @property
    def dependency(self) -> Dependency:
        return Security


UrlSandbox = CoreCodemod(
    metadata=Metadata(
        name="url-sandbox",
        summary="Sandbox URL Creation",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(
                url="https://github.com/pixee/python-security/blob/main/src/security/safe_requests/api.py"
            ),
            Reference(url="https://portswigger.net/web-security/ssrf"),
            Reference(
                url="https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html"
            ),
            Reference(
                url="https://www.rapid7.com/blog/post/2021/11/23/owasp-top-10-deep-dive-defending-against-server-side-request-forgery/"
            ),
            Reference(url="https://blog.assetnote.io/2021/01/13/blind-ssrf-chains/"),
        ],
    ),
    detector=SemgrepRuleDetector(
        """
         rules:
           - id: url-sandbox
             message: Unbounded URL creation
             severity: WARNING
             languages:
               - python
             pattern-either:
               - patterns:
                 - pattern: requests.get(...)
                 - pattern-not: requests.get("...")
                 - pattern-inside: |
                     import requests
                     ...
    """
    ),
    transformer=LibcstTransformerPipeline(UrlSandboxTransformer),
)
