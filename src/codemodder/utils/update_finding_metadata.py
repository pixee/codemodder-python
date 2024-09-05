from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from codemodder.codemods.base_codemod import ToolRule

from codemodder.codetf import ChangeSet


def update_finding_metadata(
    tool_rules: list[ToolRule],
    changesets: list[ChangeSet],
) -> list[ChangeSet]:
    if not (tool_rule_map := {rule.id: (rule.name, rule.url) for rule in tool_rules}):
        return changesets

    for changeset in changesets:
        for change in changeset.changes:
            for finding in change.findings or []:
                if finding.id in tool_rule_map:
                    finding.rule.name = tool_rule_map[finding.id][0]
                    finding.rule.url = tool_rule_map[finding.id][1]

    # TODO: eventually make this functional and return a new list
    return changesets
