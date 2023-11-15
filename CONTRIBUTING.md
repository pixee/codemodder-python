# Developing codemodder-python

## Pre-commit install

We use [pre-commit](https://pre-commit.com/) to run some quick linting such as `black`.
While pre-commit isn't configured in CI, `black` is. `pylint` and running tests are not configured
for pre-commit so commiting is fast.


## Local Development

In general you can rely on Github workflows to see how to run things like linting and tests,
but for local development here is a good workflow.

1. To use virtualenv, create an environment with `virtualenv pixeeenv` or `/usr/bin/env python3 -m venv pixeeenv`
to specify a specific Python version. If using `bash` or any compatible shell, activate with `source pixeeenv/bin/activate`. Otherwise, look at [`venv`'s documentation](https://docs.python.org/3/library/venv.html) for instructions.

1. `cd codemodder-python` and `pip install -e .` to install the package in development mode

1. Run `pip install ".[all]"` to install packages used for development and testing

1. You should now be able to run `pylint`, `pytest`, etc.


## Docker

You can build the docker image with `docker build -t codemodder .` and run it with `docker run`. You can also do
`docker run codemodder ...`
