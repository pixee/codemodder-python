import argparse
from dataclasses import dataclass
from pathlib import Path

from codemodder.registry import load_registered_codemods


@dataclass
class DocMetadata:
    """Codemod specific metadata only for documentation"""

    importance: str
    guidance_explained: str
    need_sarif: str = "No"


# codemod-specific metadata that's used only for docs, not for codemod API
CORE_CODEMODS = {
    "add-requests-timeouts": DocMetadata(
        importance="Medium",
        guidance_explained="This change makes your code safer but in some cases it may be necessary to adjust the timeout value for your particular application.",
    ),
    "django-debug-flag-on": DocMetadata(
        importance="Medium",
        guidance_explained="Django's `DEBUG` flag may be overridden somewhere else or the runtime settings file may be set with the `DJANGO_SETTINGS_MODULE` environment variable. This means that the `DEBUG` flag may intentionally be left on as a development aid.",
    ),
    "django-session-cookie-secure-off": DocMetadata(
        importance="Medium",
        guidance_explained="Django's `SESSION_COOKIE_SECURE` flag may be overridden somewhere else or the runtime settings file may be set with the `DJANGO_SETTINGS_MODULE` environment variable. This means that the flag may intentionally be left off or missing. Also some applications may still want to support pure http. This is often the case for legacy apps.",
    ),
    "enable-jinja2-autoescape": DocMetadata(
        importance="High",
        guidance_explained="This codemod protects your applications against XSS attacks. However, it's possible you would like to set the `autoescape` parameter to a custom callable.",
    ),
    "fix-mutable-params": DocMetadata(
        importance="Low",
        guidance_explained="We believe that this codemod fixes an unsafe practice and that the changes themselves are safe and reliable.",
    ),
    "harden-pyyaml": DocMetadata(
        importance="Medium",
        guidance_explained="This codemod replaces any unsafe loaders with the `SafeLoader`, which is already the recommended replacement suggested in `yaml` documentation. We believe this replacement is safe and should not result in any issues.",
    ),
    "harden-ruamel": DocMetadata(
        importance="Medium",
        guidance_explained="This codemod replaces any unsafe `typ` argument with `typ='safe'`, which makes safety explicit and is one of the recommended uses suggested in `ruamel` documentation. We believe this replacement is safe and should not result in any issues.",
    ),
    "https-connection": DocMetadata(
        importance="High",
        guidance_explained="Support for HTTPS is widespread which, save in some legacy applications, makes this change safe.",
    ),
    "jwt-decode-verify": DocMetadata(
        importance="High",
        guidance_explained="This codemod ensures your code uses all available validations when calling `jwt.decode`. We believe this replacement is safe and should not result in any issues.",
    ),
    "limit-readline": DocMetadata(
        importance="Medium",
        guidance_explained="This codemod sets a maximum of 5MB allowed per line read by default. It is unlikely but possible that your code may receive lines that are greater than 5MB _and_ you'd still be interested in reading them, so there is some nominal risk of exceptional cases.",
    ),
    "safe-lxml-parser-defaults": DocMetadata(
        importance="High",
        guidance_explained="We believe this change is safe, effective, and protects your code against very serious security attacks.",
    ),
    "safe-lxml-parsing": DocMetadata(
        importance="High",
        guidance_explained="We believe this change is safe, effective, and protects your code against very serious security attacks.",
    ),
    "order-imports": DocMetadata(
        importance="Low",
        guidance_explained="TODO SKIP FOR NOW",
    ),
    "sandbox-process-creation": DocMetadata(
        importance="High",
        guidance_explained="We believe this change is safe and effective. The behavior of sandboxing `subprocess.run` and `subprocess.call` calls will only throw `SecurityException` if they see behavior involved in malicious code execution, which is extremely unlikely to happen in normal operation.",
    ),
    "remove-unnecessary-f-str": DocMetadata(
        importance="Low",
        guidance_explained="We believe this codemod is safe and will not cause any issues.",
    ),
    "unused-imports": DocMetadata(
        importance="Low",
        guidance_explained="We believe this codemod is safe and will not cause any issues. It is important to note that importing modules may have side-effects that alter the behavior, even if unused, but we believe those cases are rare enough to be safe.",
    ),
    "requests-verify": DocMetadata(
        importance="High",
        guidance_explained="There may be times when setting `verify=False` is useful for testing though we discourage it. \nYou may also decide to set `verify=/path/to/ca/bundle`. This codemod will not attempt to modify the `verify` value if you do set it to a path.",
    ),
    "secure-flask-cookie": DocMetadata(
        importance="Medium",
        guidance_explained="Our change provides the most secure way to create cookies in Flask. However, it's possible you have configured your Flask application configurations to use secure cookies. In these cases, using the default parameters for `set_cookie` is safe.",
    ),
    "secure-random": DocMetadata(
        importance="High",
        guidance_explained="While most of the functions in the `random` module aren't cryptographically secure, there are still valid use cases for `random.random()` such as for simulations or games.",
    ),
    "secure-tempfile": DocMetadata(
        importance="High",
        guidance_explained="We believe this codemod is safe. You should review this code before merging to make sure temporary files are created, used, and closed according to your expectations.",
    ),
    "upgrade-sslcontext-minimum-version": DocMetadata(
        importance="High",
        guidance_explained="This codemod updates the minimum supported version of TLS. Since this is an important security fix and since all modern servers offer TLSv1.2, we believe this change can be safely merged without review.",
    ),
    "upgrade-sslcontext-tls": DocMetadata(
        importance="High",
        guidance_explained="This codemod updates the minimum supported version of TLS. Since this is an important security fix and since all modern servers offer TLSv1.2, we believe this change can be safely merged without review.",
    ),
    "url-sandbox": DocMetadata(
        importance="High",
        guidance_explained="""By default, the protection only weaves in 2 checks, which we believe will not cause any issues with the vast majority of code:
1. The given URL must be HTTP/HTTPS.
2. The given URL must not point to a "well-known infrastructure target", which includes things like AWS Metadata Service endpoints, and internal routers (e.g., 192.168.1.1) which are common targets of attacks.

However, on rare occasions an application may use a URL protocol like "file://" or "ftp://" in backend or middleware code.

If you want to allow those protocols, change the incoming PR to look more like this and get the best security possible:

```diff
-resp = requests.get(url)
+resp = safe_requests.get.get(url, allowed_protocols=("ftp",))
```""",
    ),
    "use-defusedxml": DocMetadata(
        importance="High",
        guidance_explained="We believe this change is safe and effective and guards against serious XML vulnerabilities. You should review this code before merging to make sure the dependency has been properly added to your project.",
    ),
    "use-walrus-if": DocMetadata(
        importance="Low",
        guidance_explained="We believe that using the walrus operator is an improvement in terms of clarity and readability. However, this change is only compatible with codebases that support Python 3.8 and later, so it requires quick validation before merging.",
    ),
    "bad-lock-with-statement": DocMetadata(
        importance="Low",
        guidance_explained="We believe this replacement is safe and should not result in any issues.",
    ),
    "sql-parameterization": DocMetadata(
        importance="High",
        guidance_explained="Python has a wealth of database drivers that all use the same `dbapi2` interface detailed in [PEP249](https://peps.python.org/pep-0249/). Different drivers may require different string tokens used for parameterization, and Python's dynamic typing makes it quite hard, and sometimes impossible, to detect which driver is being used just by looking at the code.",
    ),
    "use-generator": DocMetadata(
        importance="Low",
        guidance_explained="We believe this replacement is safe and leads to better performance.",
    ),
    "secure-flask-session-configuration": DocMetadata(
        importance="Medium",
        guidance_explained="Our change fixes explicitly insecure session configuration for a Flask application. However, there may be valid cases to use these insecure configurations, such as for testing or backward compatibility.",
    ),
    "fix-file-resource-leak": DocMetadata(
        importance="High",
        guidance_explained="We believe this change is safe and will only close file resources that are not referenced outside of the with statement block.",
    ),
    "django-receiver-on-top": DocMetadata(
        importance="Low",
        guidance_explained="We believe this change leads to the intended behavior the application and is thus safe.",
    ),
    "numpy-nan-equality": DocMetadata(
        importance="Low",
        guidance_explained="We believe any use of `==` to compare with `numpy.nan` is unintended given that it is always `False`. Thus we consider this change safe.",
    ),
    "django-json-response-type": DocMetadata(
        importance="Medium",
        guidance_explained="This change will only restrict the response type and will not alter the response data itself. Thus we deem it safe.",
    ),
    "fix-deprecated-abstractproperty": DocMetadata(
        importance="Low",
        guidance_explained="This change fixes deprecated uses and is safe.",
    ),
    "flask-json-response-type": DocMetadata(
        importance="Medium",
        guidance_explained="This change will only restrict the response type and will not alter the response data itself. Thus we deem it safe.",
    ),
    "exception-without-raise": DocMetadata(
        importance="Low",
        guidance_explained="A statement with an exception by itself has no effect. Raising the exception is most likely the intended effect and thus we deem it safe.",
    ),
    "remove-future-imports": DocMetadata(
        importance="Low",
        guidance_explained="Removing future imports is safe and will not cause any issues.",
    ),
    "literal-or-new-object-identity": DocMetadata(
        importance="Low",
        guidance_explained="Since literals and new objects have their own identities, comparisons against them using `is` operators are most likely a bug and thus we deem the change safe.",
    ),
    "subprocess-shell-false": DocMetadata(
        importance="High",
        guidance_explained="In most cases setting `shell=False` is correct and leads to much safer code. However there are valid use cases for `shell=True` when using shell functionality like pipes or wildcard is required. In such cases it is important to run only trusted, validated commands.",
    ),
    "use-set-literal": DocMetadata(
        importance="Low",
        guidance_explained="We believe this change is safe and will not cause any issues.",
    ),
    "remove-module-global": DocMetadata(
        importance="Low",
        guidance_explained="Since the `global` keyword is intended for use in non-module scopes, using it at the module scope is unnecessary.",
    ),
    "remove-debug-breakpoint": DocMetadata(
        importance="Low",
        guidance_explained="Breakpoints are generally used only for debugging and can easily be forgotten before deploying code.",
    ),
    "combine-startswith-endswith": DocMetadata(
        importance="Low",
        guidance_explained="Simplifying expressions involving `startswith` or `endswith` calls is safe.",
    ),
    "combine-isinstance-issubclass": DocMetadata(
        importance="Low",
        guidance_explained="Simplifying expressions involving `isinstance` or `issubclass` calls is safe.",
    ),
    "fix-deprecated-logging-warn": DocMetadata(
        importance="Low",
        guidance_explained="This change fixes deprecated uses and is safe.",
    ),
    "flask-enable-csrf-protection": DocMetadata(
        importance="High",
        guidance_explained="Flask views may require proper handling of CSRF to function as expected and thus this change may break some views.",
    ),
    "replace-flask-send-file": DocMetadata(
        importance="Medium",
        guidance_explained="We believe this change is safe and will not cause any issues.",
    ),
    "fix-empty-sequence-comparison": DocMetadata(
        importance="Low",
        guidance_explained="Values compared to empty sequences should be verified in case they are falsy values that are not a sequence.",
    ),
    "remove-assertion-in-pytest-raises": DocMetadata(
        importance="Low",
        guidance_explained="We believe this change is safe and will not cause any issues.",
    ),
    "fix-assert-tuple": DocMetadata(
        importance="Low",
        guidance_explained="An `assert` statement on a non-empty tuple is likely unintended and should be rewritten. However, the new change may result in assertion failures that should be reviewed.",
    ),
    "lazy-logging": DocMetadata(
        importance="Low",
        guidance_explained="We believe this change is safe and will not cause any issues.",
    ),
    "str-concat-in-sequence-literals": DocMetadata(
        importance="Low",
        guidance_explained="While string concatenation inside a sequence iterable is likely a mistake, there are instances when you may choose to use them..",
    ),
    "fix-async-task-instantiation": DocMetadata(
        importance="Low",
        guidance_explained="Manual instantiation of `asyncio.Task` is discouraged. We believe this change is safe and will not cause any issues.",
    ),
    "django-model-without-dunder-str": DocMetadata(
        importance="Low",
        guidance_explained="This codemod is a great starting point for models with few fields. We encourage you to write custom `__str__` methods that best suit your Django application.",
    ),
    "fix-hasattr-call": DocMetadata(
        importance="Low",
        guidance_explained="We believe this change is safe because using `callable` is a more reliable way to check if an object is a callable.",
    ),
    "harden-pickle-load": DocMetadata(
        importance="High",
        guidance_explained="This change may impact performance in some cases, but it is recommended when handling untrusted data.",
    ),
    "fix-dataclass-defaults": DocMetadata(
        importance="Low",
        guidance_explained="This change is safe and will prevent runtime `ValueError`.",
    ),
    "fix-missing-self-or-cls": DocMetadata(
        importance="Low",
        guidance_explained="This change is safe and will prevent errors when calling on these instance or class methods..",
    ),
    "fix-float-equality": DocMetadata(
        importance="Low",
        guidance_explained="This change makes your code more accurate but in some cases it may be necessary to adjust the `abs_tol` and `rel_tol` parameter values for your particular calculations.",
    ),
    "fix-math-isclose": DocMetadata(
        importance="Low",
        guidance_explained="This change makes your code more accurate but in some cases it may be necessary to adjust the `abs_tol` parameter value for your particular calculations.",
    ),
    "break-or-continue-out-of-loop": DocMetadata(
        importance="Low",
        guidance_explained="While this change will make the code consistent, it is likely that the `break` or `continue` statement is a symptom of an error in program logic.",
    ),
    "disable-graphql-introspection": DocMetadata(
        importance="High",
        guidance_explained="This change may disable a feature that was left on purpose. Moreover the rule added may be framework specific.",
    ),
}
DEFECTDOJO_CODEMODS = {
    "django-secure-set-cookie": DocMetadata(
        importance="Medium",
        guidance_explained="Our change provides the most secure way to create cookies in Django. However, it's possible you have configured your Django application configurations to use secure cookies. In these cases, using the default parameters for `set_cookie` is safe.",
        need_sarif="Yes (DefectDojo)",
    ),
    "avoid-insecure-deserialization": DocMetadata(
        importance="High",
        guidance_explained="This change is generally safe and will prevent deserialization vulnerabilities.",
        need_sarif="Yes (DefectDojo)",
    ),
}

SONAR_CODEMOD_NAMES = [
    "numpy-nan-equality",
    "literal-or-new-object-identity",
    "django-receiver-on-top",
    "exception-without-raise",
    "fix-assert-tuple",
    "remove-assertion-in-pytest-raises",
    "flask-json-response-type",
    "django-json-response-type",
    "jwt-decode-verify",
    "fix-missing-self-or-cls",
    "secure-tempfile",
    "secure-random",
    "enable-jinja2-autoescape",
    "url-sandbox",
    "fix-float-equality",
    "fix-math-isclose",
    "sql-parameterization",
    "django-model-without-dunder-str",
    "break-or-continue-out-of-loop",
    "disable-graphql-introspection",
]
SONAR_CODEMODS = {
    name: DocMetadata(
        importance=CORE_CODEMODS[name].importance,
        guidance_explained=CORE_CODEMODS[name].guidance_explained,
        need_sarif="Yes (Sonar)",
    )
    for name in SONAR_CODEMOD_NAMES
}

SEMGREP_CODEMOD_NAMES = [
    "url-sandbox",
    "enable-jinja2-autoescape",
    "jwt-decode-verify",
    "use-defusedxml",
    "subprocess-shell-false",
    "harden-pyyaml",
    "sql-parameterization",
]
SEMGREP_CODEMODS = {
    name: DocMetadata(
        importance=CORE_CODEMODS[name].importance,
        guidance_explained=CORE_CODEMODS[name].guidance_explained,
        need_sarif="Yes (Semgrep)",
    )
    for name in SEMGREP_CODEMOD_NAMES
} | {
    "django-secure-set-cookie": DocMetadata(
        importance="Medium",
        guidance_explained="Our change provides the most secure way to create cookies in Django. However, it's possible you have configured your Django application configurations to use secure cookies. In these cases, using the default parameters for `set_cookie` is safe.",
        need_sarif="Yes (Semgrep)",
    ),
    "rsa-key-size": DocMetadata(
        importance="Medium",
        guidance_explained="This codemod updates the key size for RSA to the `2048` recommended minimum. Since this is an important security fix that follows modern cryptographic standards, we believe this change can be safely merged without review.",
        need_sarif="Yes (Semgrep)",
    ),
    "no-csrf-exempt": DocMetadata(
        importance="Medium",
        guidance_explained="This codemod removes the `@csrf_exempt` decorator from a Django view to ensure it's protected against CSRF attacks. However, there are valid cases for using this decorator so make sure to review your application to determine if this is the case.",
        need_sarif="Yes (Semgrep)",
    ),
}
ALL_CODEMODS_METADATA = (
    CORE_CODEMODS | DEFECTDOJO_CODEMODS | SONAR_CODEMODS | SEMGREP_CODEMODS
)


def generate_docs(codemod):
    try:
        codemod_data = ALL_CODEMODS_METADATA[codemod.name]
    except KeyError as exc:
        raise KeyError(f"Must add {codemod.name} to ALL_CODEMODS_METADATA") from exc

    formatted_references = [
        f"* [{ref.description or ref.url}]({ref.url})" for ref in codemod.references
    ]
    markdown_references = "\n".join(formatted_references) or "N/A"

    # A bit of a hack but keeps the table aligned
    spacing = " " * (len(codemod.review_guidance) - 19)
    spacers = "-" * (len(codemod.review_guidance) - 19)

    output = f"""---
title: "{codemod.summary}"
sidebar_position: 1
---

## {codemod.id}

| Importance | Review Guidance     {spacing}| Requires Scanning Tool |
|------------|---------------------{spacers}|------------------------|
| {codemod_data.importance:10} | {codemod.review_guidance:19} | {codemod_data.need_sarif:22} |

{codemod.description}
If you have feedback on this codemod, [please let us know](mailto:feedback@pixee.ai)!

## F.A.Q.

### Why is this codemod marked as {codemod.review_guidance}?

{codemod_data.guidance_explained}

## Codemod Settings

N/A

## References

{markdown_references}
"""
    return output


SKIP_DOCS = ["order-imports", "unused-imports"]


def main():
    parser = argparse.ArgumentParser(
        description="Generate public docs for registered codemods."
    )

    parser.add_argument(
        "directory", type=str, help="directory path where to create doc files"
    )
    argv = parser.parse_args()
    parent_dir = Path(argv.directory)

    registry = load_registered_codemods()
    for codemod in registry.codemods:
        if codemod.name in SKIP_DOCS:
            continue

        doc = generate_docs(codemod)
        codemod_doc_name = f"{codemod.id.replace(':', '_').replace('/', '_')}.md"
        with open(parent_dir / codemod_doc_name, "w", encoding="utf-8") as f:
            f.write(doc)
