from codemodder.codemods.libcst_transformer import LibcstTransformerPipeline
from core_codemods.jwt_decode_verify import (
    JwtDecodeVerify,
    JwtDecodeVerifySASTTransformer,
)
from core_codemods.semgrep.api import SemgrepCodemod

SemgrepJwtDecodeVerify = SemgrepCodemod.from_core_codemod(
    name="jwt-decode-verify-semgrep",
    other=JwtDecodeVerify,
    rule_id="python.jwt.security.unverified-jwt-decode.unverified-jwt-decode",
    rule_name="unverified-jwt-decode",
    transformer=LibcstTransformerPipeline(JwtDecodeVerifySASTTransformer),
)
