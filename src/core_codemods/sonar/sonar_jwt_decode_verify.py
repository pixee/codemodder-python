import libcst as cst
from codemodder.codemods.base_codemod import Reference
from codemodder.codemods.sonar import SonarCodemod
from codemodder.codemods.libcst_transformer import (
    LibcstTransformerPipeline,
)
from core_codemods.jwt_decode_verify import JwtDecodeVerify, JwtDecodeVerifyTransformer


class NewTransf(JwtDecodeVerifyTransformer):
    def filter_by_result(self, node) -> bool:
        # sonar results for this rule have a start/end column
        # for the verify keyword, not for the decode call
        if self.results is None:
            return False
        match node:
            case cst.Call():
                pos_to_match = self.node_position(node)
                return any(
                    self.match_location(pos_to_match, result) for result in self.results
                )
        return False

    def match_location(self, pos, result):
        for location in result.locations:
            start_column = location.start.column
            end_column = location.end.column
            return (
                pos.start.line == location.start.line
                and pos.end.line == location.end.line
                and pos.start.column <= start_column <= pos.end.column + 1
                and pos.start.column <= end_column <= pos.end.column + 1
            )


SonarJwtDecodeVerify = SonarCodemod.from_core_codemod(
    name="jwt-decode-verify-S5659",
    other=JwtDecodeVerify,
    rules=["python:S5659"],
    new_references=[
        Reference(url="https://rules.sonarsource.com/python/RSPEC-5659/"),
    ],
    transformer=LibcstTransformerPipeline(NewTransf),
)
