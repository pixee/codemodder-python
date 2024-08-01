import re
from typing import Pattern

from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.codetf import Change, ChangeSet
from codemodder.context import CodemodExecutionContext
from codemodder.diff import create_diff
from codemodder.file_context import FileContext
from codemodder.logging import logger
from codemodder.result import Result


class RegexTransformerPipeline(BaseTransformerPipeline):
    pattern: Pattern | str
    replacement: str
    change_description: str

    def __init__(
        self, pattern: Pattern | str, replacement: str, change_description: str
    ):
        super().__init__()
        self.pattern = pattern
        self.replacement = replacement
        self.change_description = change_description

    def apply(
        self,
        context: CodemodExecutionContext,
        file_context: FileContext,
        results: list[Result] | None,
    ) -> ChangeSet | None:
        del results

        changes = []
        updated_lines = []

        original_lines = (
            file_context.file_path.read_bytes()
            .decode("utf-8")
            .splitlines(keepends=True)
        )

        for lineno, line in enumerate(original_lines):
            # TODO: use results to filter out which lines to change
            changed_line = re.sub(self.pattern, self.replacement, line)
            updated_lines.append(changed_line)
            if line != changed_line:
                changes.append(
                    Change(
                        lineNumber=lineno + 1,
                        description=self.change_description,
                        findings=file_context.get_findings_for_location(lineno),
                    )
                )

        if not changes:
            logger.debug("No changes produced for %s", file_context.file_path)
            return None

        diff = create_diff(original_lines, updated_lines)

        if not context.dry_run:
            file_context.file_path.write_bytes("".join(updated_lines).encode("utf-8"))

        return ChangeSet(
            path=str(file_context.file_path.relative_to(context.directory)),
            diff=diff,
            changes=changes,
        )
