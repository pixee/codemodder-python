import json
from pathlib import Path

import jsonschema
import pytest
import requests
from pydantic import ValidationError

from codemodder.codetf import (
    Change,
    ChangeSet,
    CodeTF,
    DiffSide,
    Finding,
    Reference,
    Result,
    Rule,
)
from codemodder.codetf.v2.codetf import (
    Action,
    DetectionTool,
    PackageAction,
    PackageResult,
    Strategy,
)
from codemodder.codetf.v3.codetf import (
    AIMetadata,
)
from codemodder.codetf.v3.codetf import Finding as FindingV3
from codemodder.codetf.v3.codetf import (
    FixStatusType,
)
from codemodder.codetf.v3.codetf import Strategy as StrategyV3
from codemodder.codetf.v3.codetf import (
    from_v2,
    from_v2_result,
    from_v2_result_per_finding,
)


@pytest.fixture(autouse=True)
def disable_write_report():
    """
    Override conftest to enable results to be written to disk for these tests.
    """


@pytest.fixture(autouse=True, scope="module")
def codetf_schema():
    schema_path = "https://raw.githubusercontent.com/pixee/codemodder-specs/main/codetf.schema.json"
    response = requests.get(schema_path)
    yield json.loads(response.text)


def test_change():
    diff = "--- a/test\n+++ b/test\n@@ -1,1 +1,1 @@\n-1\n+2\n"
    changeset = ChangeSet(
        path="test",
        diff=diff,
        changes=[
            Change(
                lineNumber=1,
                description="Change 1 to 2",
            ),
        ],
    )

    result = changeset.model_dump()

    assert result["path"] == "test"
    assert result["diff"] == diff
    assert result["changes"][0]["lineNumber"] == 1
    assert result["changes"][0]["description"] == "Change 1 to 2"
    assert result["changes"][0]["diffSide"] == DiffSide.RIGHT
    assert result["changes"][0]["properties"] is None
    assert result["changes"][0]["packageActions"] is None


@pytest.mark.parametrize("side", [DiffSide.LEFT, DiffSide.RIGHT])
def test_change_diffside(side):
    change = Change(
        lineNumber=1,
        description="Change 1 to 2",
        diffSide=side,
    )

    assert change.diffSide == side
    assert change.model_dump()["diffSide"] == side


def test_change_invalid_line_number():
    with pytest.raises(ValueError):
        Change(lineNumber=0, description="Change 1 to 2")


def test_change_empty_description():
    with pytest.raises(ValueError):
        Change(lineNumber=1, description="")


def test_change_description_optional():
    Change(lineNumber=1, description=None)


def test_write_codetf(tmpdir, mocker, codetf_schema):
    path = tmpdir / "test.codetf.json"

    assert not path.exists()

    context = mocker.MagicMock(directory=Path("/foo/bar/whatever"))
    codetf = CodeTF.build(context, 42, [], [])
    retval = codetf.write_report(path)

    assert retval == 0
    assert path.exists()

    data = path.read_text(encoding="utf-8")
    CodeTF.model_validate_json(data)

    jsonschema.validate(json.loads(data), codetf_schema)


def test_write_codetf_with_results(tmpdir, mocker, codetf_schema):
    path = tmpdir / "test.codetf.json"

    assert not path.exists()

    context = mocker.MagicMock(directory=Path("/foo/bar/whatever"))
    results = [
        Result(
            codemod="test",
            summary="test",
            description="test",
            changeset=[
                ChangeSet(
                    path="test",
                    diff="--- a/test\n+++ b/test\n@@ -1,1 +1,1 @@\n-1\n+2\n",
                    changes=[
                        Change(
                            lineNumber=1,
                            description="Change 1 to 2",
                        ),
                    ],
                ),
            ],
        )
    ]
    codetf = CodeTF.build(context, 42, [], results)
    retval = codetf.write_report(path)

    assert retval == 0
    assert path.exists()

    data = path.read_text(encoding="utf-8")
    CodeTF.model_validate_json(data)

    jsonschema.validate(json.loads(data), codetf_schema)


def test_reference_use_url_for_description():
    ref = Reference(url="https://example.com")
    assert ref.description == "https://example.com"


def test_case_insensitive_change_validation():
    json = {
        "lineNumber": 1,
        "description": "Change 1 to 2",
        "diffSide": "RIGHT",
        "packageActions": [
            {
                "action": "ADD",
                "package": "foo",
                "result": "COMPLETED",
            }
        ],
    }

    Change.model_validate(json)


@pytest.mark.parametrize("bad_value", ["MIDDLE", "middle"])
def test_still_invalidates_bad_value(bad_value):
    json = {
        "lineNumber": 1,
        "description": "Change 1 to 2",
        "diffSide": bad_value,
        "packageActions": [
            {
                "action": "ADD",
                "package": "foo",
                "result": "COMPLETED",
            }
        ],
    }

    with pytest.raises(ValidationError):
        Change.model_validate(json)


def test_v2_finding_id_optional():
    Finding(id=None, rule=Rule(id="foo", name="whatever"))


def test_v3_finding_id_not_optional():
    with pytest.raises(ValidationError):
        FindingV3(id=None, rule=Rule(id="foo", name="whatever"))  # type: ignore[arg-type]


def test_v2_result_to_v3():
    result = Result(
        codemod="codeql:java/log-injection",
        summary="Introduced protections against Log Inject    ion / Forging attacks",
        description='This change ensures that log messages can\'t contain newline characters, leaving you vulnerable to Log Forging / Log Injection.\n\nIf malicious users     can get newline characters into a log message, they can inject and forge new log entries that look like they came from the server, and trick log analysis tools, administrators, and more    . This leads to vulnerabilities like Log Injection, Log Forging, and more attacks from there.\n\nOur change simply strips out newline characters from log messages, ensuring that they can    \'t be used to forge new log entries.\n```diff\n+ import io.github.pixee.security.Newlines;\n  ...\n  String orderId = getUserOrderId();\n- log.info("User order ID: " + orderId);\n+ log.    info("User order ID: " + Newlines.stripNewlines(orderId));\n```\n',
        detectionTool=DetectionTool(name="CodeQL"),
        references=[
            Reference(
                url="https://owasp.org/www-community/attacks/Log_Inj    ection",
                description="https://owasp.org/www-community/attacks/Log_Injection",
            ),
            Reference(
                url="https://knowledge-base.secureflag.com/vulnerabilities/inadequate_input_validation/log_inject    ion_vulnerability.html",
                description="https://knowledge-base.secureflag.com/vulnerabilities/inadequate_input_validation/log_injection_vulnerability.html",
            ),
            Reference(
                url="https://cwe.mit    re.org/data/definitions/117.html",
                description="https://cwe.mitre.org/data/definitions/117.html",
            ),
        ],
        properties={},
        failedFiles=[],
        changeset=[
            ChangeSet(
                path="app/src/main/java/org/apache    /roller/planet/business/fetcher/RomeFeedFetcher.java",
                diff='--- RomeFeedFetcher.java\n+++ RomeFeedFetcher.java\n@@ -26,6 +26,7 @@\n import com.rometools.rome.io.FeedException;\n import     com.rometools.rome.io.SyndFeedInput;\n import com.rometools.rome.io.XmlReader;\n+import static io.github.pixee.security.Newlines.stripAll;\n \n import java.io.IOException;\n import java.    net.URI;\n@@ -87,7 +88,7 @@\n         }\n         \n         // fetch the feed\n-        log.debug("Fetching feed: "+feedURL);\n+        log.debug("Fetching feed: "+stripAll(feedURL));\n             SyndFeed feed;\n         try {\n             feed = fetchFeed(feedURL);',
                changes=[
                    Change(
                        lineNumber=90,
                        description="Added a call to replace any newlines the value",
                        diffSide=DiffSide.LEFT,
                        properties={},
                        packageActions=[
                            PackageAction(
                                action=Action.ADD,
                                result=PackageResult.FAILED,
                                package="pkg:maven/io.github.pixee/java-security    -toolkit@1.2.1",
                            )
                        ],
                        fixedFindings=[
                            Finding(
                                id="e5ceaca8-4a05-4f8d-ac74-6a822ac69d8f",
                                rule=Rule(
                                    id="log-injection",
                                    name="Log Injection",
                                    url="https://codeql.github.com/codeql-query-help/    java/java-log-injection/",
                                ),
                            )
                        ],
                    )
                ],
                ai=None,
                strategy=Strategy.deterministic,
                provisional=False,
                fixedFindings=None,
                fixQuality=None,
            )
        ],
        unfixedFindings=[],
    )
    assert from_v2_result(result)


def test_v2_result_to_v3_per_finding():
    result = Result(
        codemod="codeql:java/log-injection",
        summary="Introduced protections against Log Inject    ion / Forging attacks",
        description='This change ensures that log messages can\'t contain newline characters, leaving you vulnerable to Log Forging / Log Injection.\n\nIf malicious users     can get newline characters into a log message, they can inject and forge new log entries that look like they came from the server, and trick log analysis tools, administrators, and more    . This leads to vulnerabilities like Log Injection, Log Forging, and more attacks from there.\n\nOur change simply strips out newline characters from log messages, ensuring that they can    \'t be used to forge new log entries.\n```diff\n+ import io.github.pixee.security.Newlines;\n  ...\n  String orderId = getUserOrderId();\n- log.info("User order ID: " + orderId);\n+ log.    info("User order ID: " + Newlines.stripNewlines(orderId));\n```\n',
        detectionTool=DetectionTool(name="CodeQL"),
        references=[
            Reference(
                url="https://owasp.org/www-community/attacks/Log_Inj    ection",
                description="https://owasp.org/www-community/attacks/Log_Injection",
            ),
            Reference(
                url="https://knowledge-base.secureflag.com/vulnerabilities/inadequate_input_validation/log_inject    ion_vulnerability.html",
                description="https://knowledge-base.secureflag.com/vulnerabilities/inadequate_input_validation/log_injection_vulnerability.html",
            ),
            Reference(
                url="https://cwe.mit    re.org/data/definitions/117.html",
                description="https://cwe.mitre.org/data/definitions/117.html",
            ),
        ],
        properties={},
        failedFiles=[],
        changeset=[
            ChangeSet(
                path="app/src/main/java/org/apache/roller/planet/business/fetcher/RomeFeedFetcher.java",
                diff='--- RomeFeedFetcher.java\n+++ RomeFeedFetcher.java\n@@ -26,6 +26,7 @@\n import com.rometools.rome.io.FeedException;\n import com.rometools.rome.io.SyndFeedInput;\n import com.rometools.rome.io.XmlReader;\n+import static io.github.pixee.security.Newlines.stripAll;\n \n import java.io.IOException;\n import java.net.URI;\n@@ -123,7 +124,7 @@\n         }\n         \n         if(log.isDebugEnabled()) {\n-            log.debug("Subscription is: " + newSub.toString());\n+            log.debug("Subscription is: " + stripAll(newSub.toString()));\n         }\n         \n         ',
                changes=[
                    Change(
                        lineNumber=126,
                        description="Added a call to replace any newlines the value",
                        diffSide=DiffSide.LEFT,
                        properties={},
                        packageActions=[
                            PackageAction(
                                action=Action.ADD,
                                result=PackageResult.COMPLETED,
                                package="pkg:maven/io.github.pixee/java-security-toolkit@1.2.2",
                            ),
                            PackageAction(
                                action=Action.ADD,
                                result=PackageResult.COMPLETED,
                                package="pkg:maven/io.github.pixee/java-security-toolkit@1.2.2",
                            ),
                        ],
                        fixedFindings=[
                            Finding(
                                id="915a8320-3ee8-4b0e-849b-c1b380fb83e2",
                                rule=Rule(
                                    id="log-injection",
                                    name="Log Injection",
                                    url="https://codeql.github.com/codeql-query-help/java/java-log-injection/",
                                ),
                            )
                        ],
                    )
                ],
                ai=None,
                strategy=Strategy.deterministic,
                provisional=False,
                fixedFindings=[
                    Finding(
                        id="915a8320-3ee8-4b0e-849b-c1b380fb83e2",
                        rule=Rule(
                            id="log-injection",
                            name="Log Injection",
                            url="https://codeql.github.com/codeql-query-help/java/java-log-injection/",
                        ),
                    )
                ],
                fixQuality=None,
            ),
            ChangeSet(
                path="app/pom.xml",
                diff="--- app/pom.xml\n+++ app/pom.xml\n@@ -591,9 +591,12 @@\n             <version>5.3.0</version>\n             <scope>test</scope>\n         </dependency>\n+  <dependency>\n+   <groupId>io.github.pixee</groupId>\n+   <artifactId>java-security-toolkit</artifactId>\n+  </dependency>\n+ </dependencies>\n \n-    </dependencies>\n-\n     <build>\n \n         <finalName>roller</finalName>",
                changes=[
                    Change(
                        lineNumber=594,
                        description="This library holds security tools for protecting Java API calls.\n\nLicense: MIT ✅ | [Open source](https://github.com/pixee/java-security-toolkit) ✅ | [More facts](https://mvnrepository.com/artifact/io.github.pixee/java-security-toolkit/1.2.2)\n",
                        diffSide=DiffSide.RIGHT,
                        properties={"contextual_description": "true"},
                        packageActions=[],
                        fixedFindings=[],
                    )
                ],
                ai=None,
                strategy=Strategy.deterministic,
                provisional=False,
                fixedFindings=[],
                fixQuality=None,
            ),
            ChangeSet(
                path="pom.xml",
                diff="--- pom.xml\n+++ pom.xml\n@@ -48,7 +48,8 @@\n         <project.reporting.outputEncoding>UTF-8</project.reporting.outputEncoding>\n         <roller.version>6.1.5</roller.version>\n         <slf4j.version>1.7.36</slf4j.version>\n-    </properties>\n+  <versions.java-security-toolkit>1.2.2</versions.java-security-toolkit>\n+ </properties>\n \n     <modules>\n         <module>app</module>\n@@ -110,7 +111,12 @@\n                 <version>5.11.4</version>\n                 <scope>test</scope>\n             </dependency>\n-        </dependencies>\n+   <dependency>\n+    <groupId>io.github.pixee</groupId>\n+    <artifactId>java-security-toolkit</artifactId>\n+    <version>${versions.java-security-toolkit}</version>\n+   </dependency>\n+  </dependencies>\n     </dependencyManagement>\n \n </project>",
                changes=[
                    Change(
                        lineNumber=114,
                        description="This library holds security tools for protecting Java API calls.\n\nLicense: MIT ✅ | [Open source](https://github.com/pixee/java-security-toolkit) ✅ | [More facts](https://mvnrepository.com/artifact/io.github.pixee/java-security-toolkit/1.2.2)\n",
                        diffSide=DiffSide.RIGHT,
                        properties={"contextual_description": "true"},
                        packageActions=[],
                        fixedFindings=[],
                    )
                ],
                ai=None,
                strategy=Strategy.deterministic,
                provisional=False,
                fixedFindings=[],
                fixQuality=None,
            ),
        ],
        unfixedFindings=[],
    )
    fix_result = from_v2_result_per_finding(
        result,
        strategy=StrategyV3.ai,
        provisional=True,
        ai_metadata=AIMetadata(provider="pixee"),
    )
    assert fix_result
    assert len(fix_result.changeSets) == 3
    all_paths = {cs.path for cs in fix_result.changeSets}
    assert "app/pom.xml" in all_paths
    assert "pom.xml" in all_paths
    assert fix_result.fixMetadata
    # Assert that the metadata complies with the passed parameters
    assert fix_result.fixMetadata.generation.strategy == StrategyV3.ai
    assert fix_result.fixMetadata.generation.provisional
    assert fix_result.fixMetadata.generation.ai
    assert fix_result.fixMetadata.generation.ai.provider
    assert fix_result.fixMetadata.generation.ai.provider == "pixee"


def test_v2_to_v3_conversion():
    with open("tests/samples/codetfv2_sample.codetf", "r") as f:
        codetfv2 = CodeTF.model_validate_json(f.read())
        codetf = from_v2(codetfv2)

    # run
    assert codetf.run
    assert codetf.run.vendor == codetfv2.run.vendor
    assert codetf.run.tool == codetfv2.run.tool
    assert codetf.run.version == codetfv2.run.version
    assert codetf.run.elapsed == codetfv2.run.elapsed

    assert (
        codetf.run.projectmetadata
        and "directory" in codetf.run.projectmetadata.keys()
        and codetf.run.projectmetadata["directory"] == codetfv2.run.directory
    )
    assert (
        codetf.run.projectmetadata
        and "projectName" not in codetf.run.projectmetadata.keys()
        and not codetfv2.run.projectName
    )

    assert (
        codetf.run.inputmetadata
        and "commandLine" in codetf.run.inputmetadata.keys()
        and codetf.run.inputmetadata["commandLine"] == codetfv2.run.commandLine
    )
    assert not codetfv2.run.sarifs
    assert codetf.run.inputmetadata and "sarifs" not in codetf.run.inputmetadata.keys()
    # results
    v2_unfixed = [f for r in codetfv2.results for f in r.unfixedFindings or []]
    v2_fixed = [
        f
        for r in codetfv2.results
        for cs in r.changeset
        for c in cs.changes
        for f in c.fixedFindings or []
    ]
    unfixed = [
        fr for fr in codetf.results if fr.fixStatus.status == FixStatusType.failed
    ]
    fixed = [fr for fr in codetf.results if fr.fixStatus.status == FixStatusType.fixed]

    # length
    assert len(codetf.results) == len(v2_unfixed) + len(v2_fixed) == 3
    assert len(unfixed) == len(v2_unfixed) == 1
    assert len(fixed) == len(v2_fixed) == 2

    assert len(codetfv2.results) == 1
    assert len(codetfv2.results[0].changeset) == 1
    v2result = codetfv2.results[0]
    v2changeset = codetfv2.results[0].changeset[0]
    v2_finding_to_change = {
        f: c
        for r in codetfv2.results
        for cs in r.changeset
        for c in cs.changes
        for f in c.fixedFindings or []
    }

    for f in fixed:
        # fix metadata
        assert (
            f.fixMetadata
            and f.fixMetadata.generation
            and f.fixMetadata.generation.ai == v2changeset.ai
        )
        assert (
            f.fixMetadata and f.fixMetadata.id and f.fixMetadata.id == v2result.codemod
        )
        assert (
            f.fixMetadata
            and f.fixMetadata.summary
            and f.fixMetadata.summary == v2result.summary
        )
        assert (
            f.fixMetadata
            and f.fixMetadata.description
            and f.fixMetadata.description == v2result.description
        )

        # correctly associates findings to the change
        assert f.changeSets and f.changeSets[0].path == v2changeset.path
        assert f.changeSets and f.changeSets[0].diff == v2changeset.diff
        assert isinstance(f.finding, FindingV3) and f.changeSets[0].changes == [
            v2_finding_to_change[Finding(**f.finding.model_dump())].to_common()
        ]

    # unfixed metadata
    assert (
        unfixed[0].fixStatus.reason
        and unfixed[0].fixStatus.reason == v2_unfixed[0].reason
    )
    assert unfixed[0].finding == FindingV3(**v2_unfixed[0].model_dump())
