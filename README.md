<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/codemodder-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="img/codemodder-light.png">
  <img alt="Pixee Logo" src="https://github.com/pixee/pixee-cli/raw/main/img/codemodder.png">
</picture>

# codemodder-python

This is the Python version of the [Codemodder Framework](https://codemodder.io/), which builds on traditional codemod frameworks by providing
codemods with additional context and services. Codemodder plugins inject codemods with the context and services they need to perform complex transforms.

Pluggability and the complex transforms they enable distinguish codemodder codemods from traditional codemods.

Codemodder is sponsored by [pixee.ai](https://pixee.ai).

## Development Status

The `codemodder-python` project is still under heavy development. 🚧

The project includes a (growing) set of core codemods. It also supports the
development of custom codemods.

Many of the existing codemods make use of [Semgrep](https://semgrep.dev/). The
`codemodder-python` framework will support additional codemod sources in the
future.

⚠️  The custom codemod API is under heavy development and is subject to change.
The API should not be treated as stable at this time. ⚠️

## Installation

To install the package from source, use `pip`:

```
pip install .
```

## Running Locally

You can run the codemodder program with

```codemodder <directory> --output <file> ...```

```bash
codemodder --help
```

## Codemod API
<picture>
  <source srcset="img/base-codemod.jpg">
  <img alt="Base Codemod Diagram" src="https://github.com/pixee/pixee-cli/raw/main/img/base-codemod.jpg">
</picture>

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md).
