from codemodder.codemods.base_codemod import Reference
from codemodder.codemods.sonar import SonarCodemod

from core_codemods.numpy_nan_equality import (
    NumpyNanEquality,
)

SonarNumpyNanEquality = SonarCodemod.from_core_codemod(
    name="numpy-nan-equality-S6725",
    other=NumpyNanEquality,
    rules=["python:S6725"],
    new_references=[
        Reference(url="https://rules.sonarsource.com/python/type/Bug/RSPEC-6725/"),
    ],
)
