import libcst as cst

from codemodder.codemods.base_codemod import Reference
from codemodder.codemods.libcst_transformer import LibcstTransformerPipeline
from codemodder.codemods.sonar import SonarCodemod
from codemodder.result import fuzzy_column_match, same_line
from core_codemods.jwt_decode_verify import JwtDecodeVerify, JwtDecodeVerifyTransformer


class JwtDecodeVerifySonarTransformer(JwtDecodeVerifyTransformer):
    def filter_by_result(self, node) -> bool:
        """
        Special case result-matching for this rule because the sonar
        results returned have a start/end column for the verify keyword
        within the `decode` call, not for the entire call like semgrep returns.
        """
        match node:
            case cst.Call():
                pos_to_match = self.node_position(node)
                return any(
                    self.match_location(pos_to_match, result)
                    for result in self.results or []
                )
        return False

    def match_location(self, pos, result):
        return any(
            same_line(pos, location) and fuzzy_column_match(pos, location)
            for location in result.locations
        )


SonarJwtDecodeVerify = SonarCodemod.from_core_codemod(
    name="jwt-decode-verify-S5659",
    other=JwtDecodeVerify,
    rules=["python:S5659"],
    new_references=[
        Reference(url="https://rules.sonarsource.com/python/RSPEC-5659/"),
    ],
    transformer=LibcstTransformerPipeline(JwtDecodeVerifySonarTransformer),
)
