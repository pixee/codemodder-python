from codemodder.registry import CodemodCollection

from .django_debug_flag_on import DjangoDebugFlagOn
from .django_session_cookie_secure_off import DjangoSessionCookieSecureOff
from .fix_mutable_params import FixMutableParams
from .harden_pyyaml import HardenPyyaml
from .harden_ruamel import HardenRuamel
from .https_connection import HTTPSConnection
from .jwt_decode_verify import JwtDecodeVerify
from .limit_readline import LimitReadline
from .order_imports import OrderImports
from .process_creation_sandbox import ProcessSandbox
from .remove_unnecessary_f_str import RemoveUnnecessaryFStr
from .remove_unused_imports import RemoveUnusedImports
from .requests_verify import RequestsVerify
from .secure_random import SecureRandom
from .tempfile_mktemp import TempfileMktemp
from .upgrade_sslcontext_minimum_version import UpgradeSSLContextMinimumVersion
from .upgrade_sslcontext_tls import UpgradeSSLContextTLS
from .url_sandbox import UrlSandbox
from .use_walrus_if import UseWalrusIf

registry = CodemodCollection(
    origin="pixee",
    docs_module="core_codemods.docs",
    semgrep_config_module="core_codemods.semgrep",
    codemods=[
        DjangoDebugFlagOn,
        DjangoSessionCookieSecureOff,
        FixMutableParams,
        HardenPyyaml,
        HardenRuamel,
        HTTPSConnection,
        JwtDecodeVerify,
        LimitReadline,
        OrderImports,
        ProcessSandbox,
        RemoveUnnecessaryFStr,
        RemoveUnusedImports,
        RequestsVerify,
        SecureRandom,
        TempfileMktemp,
        UpgradeSSLContextMinimumVersion,
        UpgradeSSLContextTLS,
        UrlSandbox,
        UseWalrusIf,
    ],
)
