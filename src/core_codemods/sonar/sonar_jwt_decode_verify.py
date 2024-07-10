from codemodder.codemods.libcst_transformer import LibcstTransformerPipeline
from core_codemods.jwt_decode_verify import (
    JwtDecodeVerify,
    JwtDecodeVerifySASTTransformer,
)
from core_codemods.sonar.api import SonarCodemod

SonarJwtDecodeVerify = SonarCodemod.from_core_codemod(
    name="jwt-decode-verify",
    other=JwtDecodeVerify,
    rule_id="python:S5659",
    rule_name="JWT should be signed and verified",
    transformer=LibcstTransformerPipeline(JwtDecodeVerifySASTTransformer),
)
