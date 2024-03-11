from abc import ABCMeta, abstractmethod

from codemodder.codemods.base_visitor import BaseTransformer
from codemodder.codetf import ChangeSet
from codemodder.context import CodemodExecutionContext
from codemodder.file_context import FileContext
from codemodder.result import Result


class BaseTransformerPipeline(metaclass=ABCMeta):
    """
    Base class for a pipeline of transformers

    A pipeline is a list of one or more transformers that are applied in sequence.

    The transformers in a given pipeline can either be homogeneous or heterogeneous in terms of inputs and output formats accepted by each transformer. For a heterogeneous pipeline it may be necessary to implement adapter classes to convert between formats.

    Each transformer pipeline is responsible for writing results to the output files if `dry_run` is `False`.

    **NOTE**: In general, pipelines that rely on detectors will need to account for the fact that the detected results become "stale" after the application of the first transformer in the pipeline. This is not an issue for transformers that do their own detection or which are capable of adjusting the location of results
    """

    transformers: list[type[BaseTransformer]]

    def __init__(self, *transformers: type[BaseTransformer]):
        self.transformers = list(transformers)

    @abstractmethod
    def apply(
        self,
        context: CodemodExecutionContext,
        file_context: FileContext,
        results: list[Result] | None,
    ) -> ChangeSet | None:
        """
        Apply the pipeline to the given file context

        :param context: The codemod execution context
        :param file_context: The file context representing the file to transform
        :param results: The (optional) results of the detector phase

        :return: The `ChangeSet` to apply to the file, or `None` if no changes are applied

        This method is responsible for writing the results to the output files if `dry_run` is False.
        """
