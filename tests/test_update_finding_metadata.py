from codemodder.codemods.base_codemod import ToolRule
from codemodder.codetf import Change, ChangeSet, Finding, Rule
from codemodder.utils.update_finding_metadata import update_finding_metadata


def test_update_finding_metdata():
    tool_rule = ToolRule(id="rule_id", name="rule_name", url="rule_url")
    changeset = ChangeSet(
        path="",
        diff="",
        changes=[
            Change(
                lineNumber=1,
                description="foo",
                fixedFindings=[
                    Finding(id="rule_id", rule=Rule(id="rule_id", name="other_name"))
                ],
            ),
            Change(
                lineNumber=2,
                description="bar",
                fixedFindings=[
                    Finding(id="other_id", rule=Rule(id="other_id", name="other_name"))
                ],
            ),
            Change(
                lineNumber=3,
                description="baz",
            ),
        ],
    )

    new_changesets = update_finding_metadata(
        tool_rules=[tool_rule], changesets=[changeset]
    )

    assert new_changesets[0].changes[0].fixedFindings
    assert new_changesets[0].changes[0].fixedFindings[0].rule.name == "rule_name"
    assert new_changesets[0].changes[0].fixedFindings[0].rule.url == "rule_url"
    assert new_changesets[0].changes[1].fixedFindings
    assert new_changesets[0].changes[1].fixedFindings[0].rule.name == "other_name"
    assert new_changesets[0].changes[1].fixedFindings[0].rule.url is None
    assert new_changesets[0].changes[2] == changeset.changes[2]
