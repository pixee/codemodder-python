# Developing codemodder-python

## Pre-commit install

We use [pre-commit](https://pre-commit.com/) to run some quick linting such as `black`.
While pre-commit isn't configured in CI, `black` is. `pylint` and running tests are not configured
for pre-commit so commiting is fast.


## Local Development

In general you can rely on Github workflows to see how to run things like linting and tests,
but for local development here is a good workflow.

1. To use virtualenv, create an environment with `virtualenv pixeeenv` or `/usr/local/bin/python3.11 -m venv pixeeenv`
to specify a specific Python version. Activate with `pixeeenv/bin/activate`

2. `cd codemodder-python` and run `pip install -r` on all the files under `requirements/`

3. You should now be able to run `pylint`, `pytest`, etc.
