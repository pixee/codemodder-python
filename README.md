# codemodder-python

Framework for applying [codemods](https://codemodder.io/) to Python projects.

## Development Status

The `codemodder-python` project is still under development. 🚧

The project includes a (growing) set of core codemods. It also supports the
development of custom codemods.

Many of the existing codemods make use of [Semgrep](https://semgrep.dev/). The
`codemodder-python` framework will support additional codemod sources in the
future.

⚠️  The custom codemod API is under heavy development and is subject to change.
The API should not be treated as stable at this time. ⚠️

## Running Locally

You can run the codemodder program with

```python -m codemodder <directory> --output <file> ...```

```bash
python -m codemodder --help
```

## Development
See [Developer Readme](DEV_README.md)
