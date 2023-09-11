# pylint: disable=global-statement
"""Store data across an entire codemodder run."""

# Source code directory codemodder will analyze.
# Should be overridden when codemodder starts.
# TODO: we should not be managing global state at all
DIRECTORY = ""


def set_directory(path):
    global DIRECTORY
    DIRECTORY = path
