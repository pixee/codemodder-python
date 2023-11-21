from os import path
from setuptools import find_packages, setup

root_dir = path.abspath(path.dirname(__file__))

print(root_dir)

setup(
    name="test pkg",
    description="testing",
    long_description="...",
    # The project's main homepage.
    # Author details
    author="Pixee",
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">3.6",
    install_requires=[
        "protobuf>=3.12,<3.18; python_version < '3'",
        "protobuf>=3.12,<4; python_version >= '3'",
        "psutil>=5.7,<6",
        "requests>=2.4.2,<3",
    ],
    entry_points={},
)
