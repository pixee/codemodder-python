<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/codemodder-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="img/codemodder-light.png">
  <img alt="Pixee Logo" src="https://github.com/pixee/pixee-cli/raw/main/img/codemodder.png">
</picture>

# codemodder-python

This is the Python version of the [Codemodder Framework](https://codemodder.io/).

Codemodder is sponsored by [pixee.ai](https://pixee.ai).

## Development Status

As of [v0.80.0](https://github.com/pixee/codemodder-python/releases/tag/0.80.0) the codemod API is relatively stable. However, backwards compatibility between releases will not be guaranteed until version 1.0.0.


See [CHANGELOG.md](CHANGELOG.md) for detailed release notes.

## Installation

The `codemodder` package is available [on PyPI](https://pypi.org/project/codemodder/). To install, run:
```
$ pip install codemodder
```

To install the package from source, use `pip`:

```
$ pip install /path/to/codemodder-python
```

## Running Locally

The codemodder package provides an executable called `codemodder`. This should be available on your path by default after installation.

For basic usage, run the `codemodder` command with a target directory path:

```
$ codemodder /path/to/my-project
```

Note that by default `codemodder` will make changes to files in your target directory. To run `codemodder` without making updates on disk, use the `--dry-run` flag:
```
$ codemodder --dry-run /path/to/my-project
```

To list all available codemods (including any that are registered with installed plugins), use the `--list` option:
```
$ codemodder --list
```

For a full list of options, use the `--help` flag:
```
$ codemodder --help
```

## Architecture

Codemods are composed of the following key components:
* Detector
* Transformer(s)
* Metadata

<picture>
  <source srcset="img/base-codemod.jpg">
  <img alt="Base Codemod Diagram" src="https://github.com/pixee/pixee-cli/raw/main/img/base-codemod.jpg">
</picture>

## Custom Codemods

The Python codemodder supports a plugin infrastructure for custom codemods. For users interested in developing a custom codemod plugin, we recommend starting with the [Cookiecutter template](https://github.com/pixee/cookiecutter-codemodder-plugin).

## Documentation

Coming soon!

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md).
