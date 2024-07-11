from codemodder.codemods.base_codemod import ToolRule
from codemodder.codemods.libcst_transformer import LibcstTransformerPipeline
from core_codemods.jwt_decode_verify import (
    JwtDecodeVerify,
    JwtDecodeVerifySASTTransformer,
)
from core_codemods.semgrep.api import SemgrepCodemod, semgrep_url_from_id

SemgrepJwtDecodeVerify = SemgrepCodemod.from_core_codemod(
    name="jwt-decode-verify",
    other=JwtDecodeVerify,
    rules=[
        ToolRule(
            id=(
                rule_id := "python.jwt.security.unverified-jwt-decode.unverified-jwt-decode"
            ),
            name="unverified-jwt-decode",
            url=semgrep_url_from_id(rule_id),
        )
    ],
    transformer=LibcstTransformerPipeline(JwtDecodeVerifySASTTransformer),
)
