from codemodder.registry import CodemodCollection

from .add_requests_timeouts import AddRequestsTimeouts
from .django_debug_flag_on import DjangoDebugFlagOn
from .django_session_cookie_secure_off import DjangoSessionCookieSecureOff
from .enable_jinja2_autoescape import EnableJinja2Autoescape
from .fix_deprecated_abstractproperty import FixDeprecatedAbstractproperty
from .fix_mutable_params import FixMutableParams
from .harden_pyyaml import HardenPyyaml
from .harden_ruamel import HardenRuamel
from .https_connection import HTTPSConnection
from .jwt_decode_verify import JwtDecodeVerify
from .limit_readline import LimitReadline
from .lxml_safe_parser_defaults import LxmlSafeParserDefaults
from .lxml_safe_parsing import LxmlSafeParsing
from .order_imports import OrderImports
from .process_creation_sandbox import ProcessSandbox
from .remove_future_imports import RemoveFutureImports
from .remove_unnecessary_f_str import RemoveUnnecessaryFStr
from .remove_unused_imports import RemoveUnusedImports
from .requests_verify import RequestsVerify
from .secure_flask_cookie import SecureFlaskCookie
from .secure_random import SecureRandom
from .tempfile_mktemp import TempfileMktemp
from .upgrade_sslcontext_minimum_version import UpgradeSSLContextMinimumVersion
from .upgrade_sslcontext_tls import UpgradeSSLContextTLS
from .url_sandbox import UrlSandbox
from .use_defused_xml import UseDefusedXml
from .use_generator import UseGenerator
from .use_set_literal import UseSetLiteral
from .use_walrus_if import UseWalrusIf
from .with_threading_lock import WithThreadingLock
from .secure_flask_session_config import SecureFlaskSessionConfig
from .file_resource_leak import FileResourceLeak
from .django_receiver_on_top import DjangoReceiverOnTop
from .django_json_response_type import DjangoJsonResponseType
from .flask_json_response_type import FlaskJsonResponseType
from .numpy_nan_equality import NumpyNanEquality
from .sql_parameterization import SQLQueryParameterization
from .exception_without_raise import ExceptionWithoutRaise
from .literal_or_new_object_identity import LiteralOrNewObjectIdentity
from .subprocess_shell_false import SubprocessShellFalse
from .remove_module_global import RemoveModuleGlobal
from .remove_debug_breakpoint import RemoveDebugBreakpoint
from .combine_startswith_endswith import CombineStartswithEndswith
from .fix_deprecated_logging_warn import FixDeprecatedLoggingWarn
from .flask_enable_csrf_protection import FlaskEnableCSRFProtection
from .replace_flask_send_file import ReplaceFlaskSendFile
from .fix_empty_sequence_comparison import FixEmptySequenceComparison
from .remove_assertion_in_pytest_raises import RemoveAssertionInPytestRaises
from .fix_assert_tuple import FixAssertTuple
from .sonar.sonar_numpy_nan_equality import SonarNumpyNanEquality
from .sonar.sonar_literal_or_new_object_identity import SonarLiteralOrNewObjectIdentity
from .sonar.sonar_django_receiver_on_top import SonarDjangoReceiverOnTop
from .sonar.sonar_exception_without_raise import SonarExceptionWithoutRaise
from .sonar.sonar_fix_assert_tuple import SonarFixAssertTuple
from .sonar.sonar_remove_assertion_in_pytest_raises import (
    SonarRemoveAssertionInPytestRaises,
)
from .sonar.sonar_flask_json_response_type import SonarFlaskJsonResponseType
from .sonar.sonar_django_json_response_type import SonarDjangoJsonResponseType
from .lazy_logging import LazyLogging
from .str_concat_in_seq_literal import StrConcatInSeqLiteral
from .fix_async_task_instantiation import FixAsyncTaskInstantiation

registry = CodemodCollection(
    origin="pixee",
    codemods=[
        AddRequestsTimeouts,
        DjangoDebugFlagOn,
        DjangoSessionCookieSecureOff,
        EnableJinja2Autoescape,
        FixDeprecatedAbstractproperty,
        FixMutableParams,
        HardenPyyaml,
        HardenRuamel,
        HTTPSConnection,
        JwtDecodeVerify,
        LimitReadline,
        LxmlSafeParserDefaults,
        LxmlSafeParsing,
        OrderImports,
        ProcessSandbox,
        RemoveFutureImports,
        RemoveUnnecessaryFStr,
        RemoveUnusedImports,
        RequestsVerify,
        SecureFlaskCookie,
        SecureRandom,
        TempfileMktemp,
        UpgradeSSLContextMinimumVersion,
        UpgradeSSLContextTLS,
        UrlSandbox,
        UseDefusedXml,
        UseGenerator,
        UseSetLiteral,
        UseWalrusIf,
        WithThreadingLock,
        SQLQueryParameterization,
        SecureFlaskSessionConfig,
        SubprocessShellFalse,
        FileResourceLeak,
        DjangoReceiverOnTop,
        NumpyNanEquality,
        DjangoJsonResponseType,
        FlaskJsonResponseType,
        ExceptionWithoutRaise,
        LiteralOrNewObjectIdentity,
        RemoveModuleGlobal,
        RemoveDebugBreakpoint,
        CombineStartswithEndswith,
        FixDeprecatedLoggingWarn,
        FlaskEnableCSRFProtection,
        ReplaceFlaskSendFile,
        FixEmptySequenceComparison,
        RemoveAssertionInPytestRaises,
        FixAssertTuple,
        LazyLogging,
        StrConcatInSeqLiteral,
        FixAsyncTaskInstantiation,
    ],
)

sonar_registry = CodemodCollection(
    origin="sonar",
    codemods=[
        SonarNumpyNanEquality,
        SonarLiteralOrNewObjectIdentity,
        SonarDjangoReceiverOnTop,
        SonarExceptionWithoutRaise,
        SonarFixAssertTuple,
        SonarRemoveAssertionInPytestRaises,
        SonarFlaskJsonResponseType,
        SonarDjangoJsonResponseType,
    ],
)
