from codemodder.registry import CodemodCollection

from .add_requests_timeouts import AddRequestsTimeouts
from .break_or_continue_out_of_loop import BreakOrContinueOutOfLoop
from .combine_isinstance_issubclass import CombineIsinstanceIssubclass
from .combine_startswith_endswith import CombineStartswithEndswith
from .defectdojo.semgrep.avoid_insecure_deserialization import (
    AvoidInsecureDeserialization,
)
from .defectdojo.semgrep.django_secure_set_cookie import DjangoSecureSetCookie
from .disable_graphql_introspection import DisableGraphQLIntrospection
from .django_debug_flag_on import DjangoDebugFlagOn
from .django_json_response_type import DjangoJsonResponseType
from .django_model_without_dunder_str import DjangoModelWithoutDunderStr
from .django_receiver_on_top import DjangoReceiverOnTop
from .django_session_cookie_secure_off import DjangoSessionCookieSecureOff
from .enable_jinja2_autoescape import EnableJinja2Autoescape
from .exception_without_raise import ExceptionWithoutRaise
from .file_resource_leak import FileResourceLeak
from .fix_assert_tuple import FixAssertTuple
from .fix_async_task_instantiation import FixAsyncTaskInstantiation
from .fix_dataclass_defaults import FixDataclassDefaults
from .fix_deprecated_abstractproperty import FixDeprecatedAbstractproperty
from .fix_deprecated_logging_warn import FixDeprecatedLoggingWarn
from .fix_empty_sequence_comparison import FixEmptySequenceComparison
from .fix_float_equality import FixFloatEquality
from .fix_hasattr_call import TransformFixHasattrCall
from .fix_math_isclose import FixMathIsClose
from .fix_missing_self_or_cls import FixMissingSelfOrCls
from .fix_mutable_params import FixMutableParams
from .flask_enable_csrf_protection import FlaskEnableCSRFProtection
from .flask_json_response_type import FlaskJsonResponseType
from .harden_pickle_load import HardenPickleLoad
from .harden_pyyaml import HardenPyyaml
from .harden_ruamel import HardenRuamel
from .https_connection import HTTPSConnection
from .jwt_decode_verify import JwtDecodeVerify
from .lazy_logging import LazyLogging
from .limit_readline import LimitReadline
from .literal_or_new_object_identity import LiteralOrNewObjectIdentity
from .lxml_safe_parser_defaults import LxmlSafeParserDefaults
from .lxml_safe_parsing import LxmlSafeParsing
from .numpy_nan_equality import NumpyNanEquality
from .order_imports import OrderImports
from .process_creation_sandbox import ProcessSandbox
from .remove_assertion_in_pytest_raises import RemoveAssertionInPytestRaises
from .remove_debug_breakpoint import RemoveDebugBreakpoint
from .remove_future_imports import RemoveFutureImports
from .remove_module_global import RemoveModuleGlobal
from .remove_unnecessary_f_str import RemoveUnnecessaryFStr
from .remove_unused_imports import RemoveUnusedImports
from .replace_flask_send_file import ReplaceFlaskSendFile
from .requests_verify import RequestsVerify
from .secure_flask_cookie import SecureFlaskCookie
from .secure_flask_session_config import SecureFlaskSessionConfig
from .secure_random import SecureRandom
from .semgrep.semgrep_django_secure_set_cookie import SemgrepDjangoSecureSetCookie
from .semgrep.semgrep_enable_jinja2_autoescape import SemgrepEnableJinja2Autoescape
from .semgrep.semgrep_harden_pyyaml import SemgrepHardenPyyaml
from .semgrep.semgrep_jwt_decode_verify import SemgrepJwtDecodeVerify
from .semgrep.semgrep_no_csrf_exempt import SemgrepNoCsrfExempt
from .semgrep.semgrep_rsa_key_size import SemgrepRsaKeySize
from .semgrep.semgrep_sql_parametrization import SemgrepSQLParameterization
from .semgrep.semgrep_subprocess_shell_false import SemgrepSubprocessShellFalse
from .semgrep.semgrep_url_sandbox import SemgrepUrlSandbox
from .semgrep.semgrep_use_defused_xml import SemgrepUseDefusedXml
from .sonar.sonar_break_or_continue_out_of_loop import SonarBreakOrContinueOutOfLoop
from .sonar.sonar_disable_graphql_introspection import SonarDisableGraphQLIntrospection
from .sonar.sonar_django_json_response_type import SonarDjangoJsonResponseType
from .sonar.sonar_django_model_without_dunder_str import (
    SonarDjangoModelWithoutDunderStr,
)
from .sonar.sonar_django_receiver_on_top import SonarDjangoReceiverOnTop
from .sonar.sonar_enable_jinja2_autoescape import SonarEnableJinja2Autoescape
from .sonar.sonar_exception_without_raise import SonarExceptionWithoutRaise
from .sonar.sonar_fix_assert_tuple import SonarFixAssertTuple
from .sonar.sonar_fix_float_equality import SonarFixFloatEquality
from .sonar.sonar_fix_math_isclose import SonarFixMathIsClose
from .sonar.sonar_fix_missing_self_or_cls import SonarFixMissingSelfOrCls
from .sonar.sonar_flask_json_response_type import SonarFlaskJsonResponseType
from .sonar.sonar_jwt_decode_verify import SonarJwtDecodeVerify
from .sonar.sonar_literal_or_new_object_identity import SonarLiteralOrNewObjectIdentity
from .sonar.sonar_numpy_nan_equality import SonarNumpyNanEquality
from .sonar.sonar_remove_assertion_in_pytest_raises import (
    SonarRemoveAssertionInPytestRaises,
)
from .sonar.sonar_secure_random import SonarSecureRandom
from .sonar.sonar_sql_parameterization import SonarSQLParameterization
from .sonar.sonar_tempfile_mktemp import SonarTempfileMktemp
from .sonar.sonar_url_sandbox import SonarUrlSandbox
from .sql_parameterization import SQLQueryParameterization
from .str_concat_in_seq_literal import StrConcatInSeqLiteral
from .subprocess_shell_false import SubprocessShellFalse
from .tempfile_mktemp import TempfileMktemp
from .upgrade_sslcontext_minimum_version import UpgradeSSLContextMinimumVersion
from .upgrade_sslcontext_tls import UpgradeSSLContextTLS
from .url_sandbox import UrlSandbox
from .use_defused_xml import UseDefusedXml
from .use_generator import UseGenerator
from .use_set_literal import UseSetLiteral
from .use_walrus_if import UseWalrusIf
from .with_threading_lock import WithThreadingLock

registry = CodemodCollection(
    origin="pixee",
    codemods=[
        AddRequestsTimeouts,
        DjangoDebugFlagOn,
        DjangoSessionCookieSecureOff,
        EnableJinja2Autoescape,
        FixDeprecatedAbstractproperty,
        FixMutableParams,
        HardenPickleLoad,
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
        CombineIsinstanceIssubclass,
        FixDeprecatedLoggingWarn,
        FlaskEnableCSRFProtection,
        ReplaceFlaskSendFile,
        FixEmptySequenceComparison,
        RemoveAssertionInPytestRaises,
        FixAssertTuple,
        FixFloatEquality,
        LazyLogging,
        StrConcatInSeqLiteral,
        FixAsyncTaskInstantiation,
        DjangoModelWithoutDunderStr,
        TransformFixHasattrCall,
        FixDataclassDefaults,
        FixMissingSelfOrCls,
        FixMathIsClose,
        BreakOrContinueOutOfLoop,
        DisableGraphQLIntrospection,
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
        SonarJwtDecodeVerify,
        SonarFixMissingSelfOrCls,
        SonarTempfileMktemp,
        SonarSecureRandom,
        SonarEnableJinja2Autoescape,
        SonarUrlSandbox,
        SonarFixFloatEquality,
        SonarFixMathIsClose,
        SonarSQLParameterization,
        SonarDjangoModelWithoutDunderStr,
        SonarBreakOrContinueOutOfLoop,
        SonarDisableGraphQLIntrospection,
    ],
)

defectdojo_registry = CodemodCollection(
    origin="defectdojo",
    codemods=[
        AvoidInsecureDeserialization,
        DjangoSecureSetCookie,
    ],
)

semgrep_registry = CodemodCollection(
    origin="semgrep",
    codemods=[
        SemgrepUrlSandbox,
        SemgrepEnableJinja2Autoescape,
        SemgrepNoCsrfExempt,
        SemgrepJwtDecodeVerify,
        SemgrepUseDefusedXml,
        SemgrepSubprocessShellFalse,
        SemgrepDjangoSecureSetCookie,
        SemgrepHardenPyyaml,
        SemgrepRsaKeySize,
        SemgrepSQLParameterization,
    ],
)
