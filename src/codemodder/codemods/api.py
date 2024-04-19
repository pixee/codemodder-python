from abc import ABCMeta
from typing import Callable

import libcst as cst

from codemodder.codemods.base_codemod import (  # noqa: F401
    BaseCodemod,
    Metadata,
    Reference,
    ReviewGuidance,
    ToolMetadata,
    ToolRule,
)
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.semgrep import SemgrepRuleDetector
from codemodder.file_context import FileContext  # noqa: F401


class SimpleCodemod(LibcstResultTransformer, metaclass=ABCMeta):
    """
    Base class for codemods with a single detector and transformer

    Child classes must implement the following attributes:
    - metadata: Metadata
    - codemod_base: type[BaseCodemod]
    """

    metadata: Metadata
    detector_pattern: str
    on_result_found: Callable[[cst.CSTNode, cst.CSTNode], cst.CSTNode]

    codemod_base: type[BaseCodemod]

    def __init__(self, *args, **kwargs):
        """Obfuscates the type of the constructor to make the type checker happy"""
        super().__init__(*args, **kwargs)

    def __new__(cls, *args, **kwargs):
        del args

        if kwargs.get("_transformer", False):
            return super().__new__(cls)

        return cls.codemod_base(
            metadata=cls.metadata,
            detector=(
                SemgrepRuleDetector(cls.detector_pattern)
                if getattr(cls, "detector_pattern", None)
                else None
            ),
            # This allows the transformer to inherit all the methods of the class itself
            transformer=LibcstTransformerPipeline(cls),
        )
