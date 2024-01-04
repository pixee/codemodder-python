# CHANGELOG

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
