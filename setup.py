from setuptools import setup

setup(
    name="codemodder-python",
    version="0.1.0",  # __VERSION__
    packages=["src"],
    entry_points={"console_scripts": ["src = codemodder.__main__:run"]},
)
