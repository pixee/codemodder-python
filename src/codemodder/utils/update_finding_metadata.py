from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from codemodder.codemods.base_codemod import ToolRule

from codemodder.codetf import Change, ChangeSet


def update_finding_metadata(
    tool_rules: list[ToolRule],
    changesets: list[ChangeSet],
) -> list[ChangeSet]:
    if not (tool_rule_map := {rule.id: (rule.name, rule.url) for rule in tool_rules}):
        return changesets

    new_changesets: list[ChangeSet] = []
    for changeset in changesets:
        new_changes: list[Change] = []
        for change in changeset.changes:
            new_changes.append(
                change.with_findings(
                    [
                        (
                            finding.with_rule(*tool_rule_map[finding.rule.id])
                            if finding.rule.id in tool_rule_map
                            else finding
                        )
                        for finding in change.fixedFindings or []
                    ]
                    or None
                )
            )
        new_changesets.append(changeset.with_changes(new_changes))

    return new_changesets
