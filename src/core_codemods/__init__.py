from codemodder.registry import CodemodCollection

from .django_debug_flag_on import DjangoDebugFlagOn
from .django_session_cookie_secure_off import DjangoSessionCookieSecureOff
from .enable_jinja2_autoescape import EnableJinja2Autoescape
from .fix_mutable_params import FixMutableParams
from .harden_pyyaml import HardenPyyaml
from .harden_ruamel import HardenRuamel
from .https_connection import HTTPSConnection
from .jwt_decode_verify import JwtDecodeVerify
from .limit_readline import LimitReadline
from .lxml_safe_parser_defaults import LxmlSafeParserDefaults
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
from .with_threading_lock import WithThreadingLock

registry = CodemodCollection(
    origin="pixee",
    docs_module="core_codemods.docs",
    semgrep_config_module="core_codemods.semgrep",
    codemods=[
        DjangoDebugFlagOn,
        DjangoSessionCookieSecureOff,
        EnableJinja2Autoescape,
        FixMutableParams,
        HardenPyyaml,
        HardenRuamel,
        HTTPSConnection,
        JwtDecodeVerify,
        LimitReadline,
        LxmlSafeParserDefaults,
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
        WithThreadingLock,
    ],
)
