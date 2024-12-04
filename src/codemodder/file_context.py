from dataclasses import dataclass, field
from pathlib import Path

from codemodder.codetf import Change, ChangeSet, Finding, UnfixedFinding
from codemodder.dependency import Dependency
from codemodder.logging import logger
from codemodder.result import Result
from codemodder.utils.timer import Timer


@dataclass
class FileContext:
    """
    Extra context for running codemods on a given file based on the cli parameters.
    """

    base_directory: Path
    file_path: Path
    line_exclude: list[int] = field(default_factory=list)
    line_include: list[int] = field(default_factory=list)
    results: list[Result] | None = field(default_factory=list)
    dependencies: set[Dependency] = field(default_factory=set)
    codemod_changes: list[Change] = field(default_factory=list)
    unfixed_findings: list[UnfixedFinding] = field(default_factory=list)
    changesets: list[ChangeSet] = field(default_factory=list)
    failures: list[Path] = field(default_factory=list)
    timer: Timer = field(default_factory=Timer)

    def add_dependency(self, dependency: Dependency):
        self.dependencies.add(dependency)

    def add_changeset(self, result: ChangeSet):
        self.changesets.append(result)

    def add_failure(self, filename: Path, reason: str):
        self.failures.append(filename)
        self.add_unfixed_findings(self.get_all_findings(), reason, 0)

    def add_unfixed_findings(
        self, findings: list[Finding], reason: str, line_number: int | None = None
    ):
        self.unfixed_findings.extend(
            [
                finding.to_unfixed_finding(
                    path=str(self.file_path.relative_to(self.base_directory)),
                    line_number=line_number,
                    reason=reason,
                )
                for finding in findings
            ]
        )

    def get_findings_for_location(self, line_number: int) -> list[Finding]:
        return [
            result.finding
            for result in (self.results or [])
            if result.finding is not None
            and (
                any(
                    location.start.line <= line_number <= location.end.line
                    for location in result.locations
                )
                or any(
                    location.start.line <= line_number <= location.end.line
                    for codeflow in result.codeflows
                    for location in codeflow
                )
            )
        ]

    def match_findings(self, line_numbers):
        """
        Find the first finding that applies to any of the changed lines
        NOTE: this is necessarily heuristic and may not always be correct
        """
        findings = next(
            (
                findings
                for line in line_numbers
                if (findings := self.get_findings_for_location(line))
            ),
            None,
        )

        if (
            findings is None
            and line_numbers
            and any(result.finding for result in self.results or [])
        ):
            logger.debug(
                "Did not match line_numbers %s with one of these results: '%s'",
                line_numbers,
                self.results,
            )
        return findings

    def get_all_findings(self):
        return [
            result.finding
            for result in (self.results or [])
            if result.finding is not None
        ]
