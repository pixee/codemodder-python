from pathlib import Path

from codemodder.codemods.api import BaseCodemod
from codemodder.codemods.api import SimpleCodemod as _SimpleCodemod
from codemodder.codemods.base_codemod import Metadata
from codemodder.codemods.base_detector import BaseDetector
from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.context import CodemodExecutionContext


class CoreCodemod(BaseCodemod):
    """
    Base class for all core codemods provided by this package.
    """

    @property
    def origin(self):
        return "pixee"

    @property
    def docs_module_path(self):
        return "core_codemods.docs"


class SASTCodemod(CoreCodemod):
    requested_rules: list[str]

    def __init__(
        self,
        *,
        metadata: Metadata,
        detector: BaseDetector | None = None,
        transformer: BaseTransformerPipeline,
        default_extensions: list[str] | None = None,
        requested_rules: list[str] | None = None,
    ):
        super().__init__(
            metadata=metadata,
            detector=detector,
            transformer=transformer,
            default_extensions=default_extensions,
        )
        self.requested_rules = []
        if requested_rules:
            self.requested_rules.extend(requested_rules)

    def apply(
        self,
        context: CodemodExecutionContext,
        files_to_analyze: list[Path],
    ) -> None:
        self._apply(context, files_to_analyze, self.requested_rules)


class SimpleCodemod(_SimpleCodemod):
    """
    Base class for all core codemods with a single detector and transformer.
    """

    codemod_base = CoreCodemod
