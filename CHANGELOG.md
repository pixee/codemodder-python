# CHANGELOG

This file contains change logs for v0.81.0 and earlier.

See [GitHub Releases](https://github.com/pixee/codemodder-python/releases) for the most up-to-date change logs.

## 0.81.0 (2024-02-19)

### New
* New codemod: `fix-async-task-instantiation`

### Fix
* Remove unused fields from `CodemodCollection` API
* Fix edge case in `sql-parameterization` to remove empty string variable from query


## 0.80.0 (2024-02-16)

### New

* Accept Sonar security JSON for detection (#223)
* New `BaseCodemod` API (#213)
* New codemod: `fix-assert-tuple`
* New codemod: `fix-empty-sequence-comparison`
* New codemod: `lazy-logging`
* New codemod: `remove-assertion-in-pytest-raises`
* New codemod: `str-concat-in-sequence-literals`
* Handle `httpx` in `requests-verify` codemod (#243)

### Fix
* Handle multiple blocks in `fix-file-resource-leak`

## 0.72.0 (2024-02-13)

### New
* Respect `#noqa` annotations for `subprocess-shell-false` codemod (#259)
* Additional checks to prevent false positives in `flask-json-content-type` (#257)

### Fixed
* Avoid incorrect changes in `requests-timeout` codemod (#256)
* Enable `fix-mutable-params` codemod to correctly handle single-statement functions (#255)

## 0.71.0 (2024-02-06)

### New

* Add `diffSide` field to change entries in CodeTF

## 0.70.3 (2024-01-31)

### Fixed

* Additional test directory patterns to ignore

## 0.70.2 (2024-01-30)

### Fixed

* Fix `secure-random` codemod: ignore `random.SystemRandom`

## 0.70.1 (2024-01-26)

### Fixed

* Fix path inclusion behavior

## 0.70.0 (2024-01-17)

### New

* `remove-debug-breakpoint` codemod
* `combine-startswith-endswith` codemod
* `replace-flask-send-file` codemod
* `fix-deprecated-logging-warn` codemod
* `flask-enable-csrf-protection` codemod
* Update `harden-pyyaml` to fix custom loader classes that inherit unsafe loaders

### Fixed

* Add proper inclusion/exclusion filter to codemods that were missing it

## 0.69.0 (2024-01-04)

### New

* `use-set-literal` codemod
* `remove-module-global` codemod
* `subprocess-shell-false` codemod
* Better formatting for dependency updates to `setup.py`
* Add expression propagation to `literal-or-new-object-identity`

### Fixed

## 0.68.1 (2023-12-22)

### Fixed
* Fix regression in dependency manager: do not re-add existing dependency

## 0.68.0 (2023-12-21)

### New

* `literal-or-new-object-identity` codemod
* `remove-future-imports` codemod
* `add-requests-timeout` codemod
* `exception-without-raise` codemod
* Better heuristic for detecting which dependency files to update
* Add detailed description to CodeTF about dependency update (or failure)

### Fixed

## 0.67.0 (2023-12-13)

### New
* `flask-json-response-type` codemod
* Support for `Popen` in `sandbox-process-creation`

### Fixed
* Update example in `url-sandbox` documentation

## 0.66.0 (2023-12-12)

### New
* `fix-deprecated-abstractproperty` codemod
* Add inequality support to `numpy-nan-equality`
* Add `--sonar-issues-json` CLI flag for compatibility
* Make `--output` CLI flag optional to align with spec
* Implement `use-walrus-if` codemod without semgrep
* Exclude `order-imports` and `unused-imports` by default
* Better description for `remove-unnecessary-f-str`

### Fixed
* Better handling of edge cases in `use-walrus-if`

## 0.65.0 (2023-12-4)

### New
* `django-json-response-type` codemod
* `django-receiver-on-top` codemod
* `numpy-nan-equality` codemod
* `fix-file-resource-leak` codemod
* Add support for `aiohttp2_jinja` to `enable-jinja2-autoescape`
* Implement `--describe` CLI flag

## 0.64.4 (2023-11-20)

### Fixed
* Update email alias

## 0.64.3 (2023-11-17)

### Fixed
* Do not modify body of abstract methods for `fix-mutable-params`
* Preserve `Optional` type annotation if present in `fix-mutable-params`

## 0.64.2 (2023-11-17)

### Fixed
* Handle updates to `requirements.txt` files without trailing newlines

## 0.64.1 (2023-11-17)

### Fixed
* Ignore hardcoded URLs for detecting `url-sandbox`

## 0.64.0 (2023-11-16)

### New
* `use-generator` codemod
* Move extra dependencies to `pyproject.toml`

## 0.63.0 (2023-11-14)

### New
* `sql-parametrization` codemod
* Updates to package metadata for release to PyPI

### Fixed
* Generate CodeTF even when no files/codemods match
* Preserve custom loaders with `harden-pyyaml`

## 0.62.0 (2023-11-12)

### New
* Optimization: initial scan with semgrep to filter potential results

## 0.61.3 (2023-11-3)

### Fixed
* Work around bug in `difflib` for producting CodeTF diffs

## 0.61.2 (2023-11-1)

### Fixed
* Updates to internal release process

## 0.61.1 (2023-11-1)

### Fixed
* Fixed import alias case for `harden-pyyaml`, `secure-tempfile`, and `upgrade-sslcontext-minimum-version`
* Handle missing terminating newline in dependency manager
