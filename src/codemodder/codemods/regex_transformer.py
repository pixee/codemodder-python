import re
from typing import Pattern

from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.codetf import Change, ChangeSet, Strategy
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

    def _apply_regex(self, line):
        return re.sub(self.pattern, self.replacement, line)

    def _apply(self, original_lines, file_context, results):
        del results

        changes = []
        updated_lines = []

        for lineno, line in enumerate(original_lines):
            changed_line = self._apply_regex(line)
            updated_lines.append(changed_line)
            if line != changed_line:
                changes.append(
                    Change(
                        lineNumber=lineno + 1,
                        description=self.change_description,
                        fixedFindings=file_context.get_findings_for_location(lineno),
                    )
                )
        return changes, updated_lines

    def apply(
        self,
        context: CodemodExecutionContext,
        file_context: FileContext,
        results: list[Result] | None,
    ) -> ChangeSet | None:

        original_lines = (
            file_context.file_path.read_bytes()
            .decode("utf-8")
            .splitlines(keepends=True)
        )

        changes, updated_lines = self._apply(original_lines, file_context, results)

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
            strategy=Strategy.deterministic,
            provisional=False,
        )


class SastRegexTransformerPipeline(RegexTransformerPipeline):
    def line_matches_result(self, lineno: int, result_linenums: list[int]) -> bool:
        return lineno in result_linenums

    def report_unfixed(self, file_context: FileContext, line_number: int, reason: str):
        findings = file_context.get_findings_for_location(line_number)
        file_context.add_unfixed_findings(findings, reason, line_number)

    def _apply(self, original_lines, file_context, results):
        changes = []
        updated_lines = []
        if results is not None and not results:
            return changes, updated_lines

        result_linenums = [
            location.start.line for result in results for location in result.locations
        ]
        for lineno, line in enumerate(original_lines):
            if self.line_matches_result(one_idx_lineno := lineno + 1, result_linenums):
                changed_line = self._apply_regex(line)
                updated_lines.append(changed_line)
                if line == changed_line:
                    logger.warning("Unable to update html line: %s", line)
                    self.report_unfixed(
                        file_context,
                        one_idx_lineno,
                        reason="Unable to update html line",
                    )
                    continue

                changes.append(
                    Change(
                        lineNumber=lineno + 1,
                        description=self.change_description,
                        fixedFindings=file_context.get_findings_for_location(lineno),
                    )
                )

            else:
                updated_lines.append(line)
        return changes, updated_lines
