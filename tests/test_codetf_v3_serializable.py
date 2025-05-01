import json

from codemodder.codetf.common import Change, DiffSide, Finding, FixQuality, Rating, Rule
from codemodder.codetf.v3.codetf import (
    AIMetadata,
    ChangeSet,
    CodeTF,
    FixMetadata,
    FixResult,
    FixStatus,
    FixStatusType,
    GenerationMetadata,
    Reference,
    Run,
    Strategy,
)


def test_codetf_v3_is_json_serializable():
    """Test that the CodeTF v3 model can be serialized to JSON."""
    # Create a minimal valid CodeTF instance
    rule = Rule(id="TEST001", name="Test Rule")
    finding = Finding(id="finding-123", rule=rule)

    # Create a minimal valid Run instance
    run = Run(vendor="test-vendor", tool="test-tool", version="1.0.0")

    # Create a minimal FixResult with status=skipped (to avoid validation requirements for fixed)
    fix_status = FixStatus(status=FixStatusType.skipped, reason="Test reason")
    fix_result = FixResult(finding=finding, fixStatus=fix_status)

    # Create a CodeTF instance
    codetf = CodeTF(run=run, results=[fix_result])

    # Test JSON serialization
    json_str = json.dumps(codetf.model_dump())

    # Verify that we can parse it back
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    assert "run" in parsed
    assert "results" in parsed
    assert parsed["run"]["vendor"] == "test-vendor"
    assert parsed["run"]["tool"] == "test-tool"
    assert parsed["run"]["version"] == "1.0.0"

    # Verify that CodeTF can be reconstructed from the JSON
    codetf_from_json = CodeTF.model_validate_json(json_str)
    assert isinstance(codetf_from_json, CodeTF)
    assert codetf_from_json.run.vendor == codetf.run.vendor
    assert codetf_from_json.run.tool == codetf.run.tool
    assert codetf_from_json.run.version == codetf.run.version
    assert len(codetf_from_json.results) == len(codetf.results)


def test_codetf_v3_complex_instance_is_serializable():
    """Test that a more complex CodeTF v3 model can be serialized to JSON."""
    # Create a rule and finding
    rule = Rule(id="TEST001", name="Test Rule", url="https://example.com/rules/TEST001")
    finding = Finding(id="finding-123", rule=rule)

    # Create a Run instance with all fields
    run = Run(
        vendor="test-vendor",
        tool="test-tool",
        version="1.0.0",
        projectMetadata="Test Project",
        elapsed=1000,
        inputMetadata={"args": ["--fix", "--all"]},
        analysisMetadata={"memory": "512MB"},
    )

    # Create a Change
    change = Change(
        lineNumber=42,
        description="Fixed vulnerability",
        diffSide=DiffSide.RIGHT,
        properties={"severity": "high"},
    )

    # Create a ChangeSet
    change_set = ChangeSet(
        path="/path/to/file.py",
        diff="@@ -42,1 +42,1 @@\n-unsafe_code()\n+safe_code()",
        changes=[change],
    )

    # Create fix metadata
    reference = Reference(url="https://example.com/vuln/123")
    ai_metadata = AIMetadata(
        provider="test-provider",
        models=["gpt-4"],
        total_tokens=100,
        completion_tokens=50,
        prompt_tokens=50,
    )
    generation_metadata = GenerationMetadata(
        strategy=Strategy.hybrid, ai=ai_metadata, provisional=False
    )
    fix_metadata = FixMetadata(
        id="test-fix",
        summary="Fixed security vulnerability",
        description="Replaced unsafe code with safe code",
        references=[reference],
        generation=generation_metadata,
    )

    # Create quality ratings
    fix_quality = FixQuality(
        safetyRating=Rating(score=5, description="Very safe"),
        effectivenessRating=Rating(score=4, description="Effective"),
        cleanlinessRating=Rating(score=5, description="Very clean"),
    )

    # Create FixStatus for a fixed finding
    fix_status = FixStatus(
        status=FixStatusType.fixed, details="Successfully fixed the vulnerability"
    )

    # Create FixResult
    fix_result = FixResult(
        finding=finding,
        fixStatus=fix_status,
        changeSets=[change_set],
        fixMetadata=fix_metadata,
        fixQuality=fix_quality,
        reasoningSteps=["Identified unsafe code", "Replaced with safe alternative"],
    )

    # Create the CodeTF instance
    codetf = CodeTF(run=run, results=[fix_result])

    # Test JSON serialization
    json_str = json.dumps(codetf.model_dump())

    # Verify that we can parse it back
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)

    # Verify that CodeTF can be reconstructed from the JSON
    codetf_from_json = CodeTF.model_validate_json(json_str)
    assert isinstance(codetf_from_json, CodeTF)

    # Verify a few complex fields to ensure proper serialization
    assert codetf_from_json.results[0].fixMetadata is not None
    assert (
        codetf_from_json.results[0].fixMetadata.generation.strategy == Strategy.hybrid
    )
    assert codetf_from_json.results[0].fixQuality is not None
    assert codetf_from_json.results[0].fixQuality.safetyRating.score == 5
    assert codetf_from_json.results[0].changeSets[0].changes[0].lineNumber == 42


def test_codetf_v3_exclude_none_values():
    """Test that None values are excluded from the JSON output."""
    # Create a minimal valid CodeTF instance
    rule = Rule(id="TEST001", name="Test Rule")
    finding = Finding(id="finding-123", rule=rule)

    # Create a Run with optional fields set to None
    run = Run(
        vendor="test-vendor",
        tool="test-tool",
        version="1.0.0",
        projectMetadata=None,
        elapsed=None,
        inputMetadata=None,
        analysisMetadata=None,
    )

    # Create a FixResult with optional fields set to None
    fix_status = FixStatus(status=FixStatusType.skipped, reason=None, details=None)
    fix_result = FixResult(
        finding=finding,
        fixStatus=fix_status,
        changeSets=[],
        fixMetadata=None,
        fixQuality=None,
        reasoningSteps=None,
    )

    # Create a CodeTF instance
    codetf = CodeTF(run=run, results=[fix_result])

    # Serialize with exclude_none=True
    json_str = json.dumps(codetf.model_dump(exclude_none=True))
    parsed = json.loads(json_str)

    # Verify None fields are excluded
    assert "projectMetadata" not in parsed["run"]
    assert "elapsed" not in parsed["run"]
    assert "inputMetadata" not in parsed["run"]
    assert "analysisMetadata" not in parsed["run"]

    assert "reason" not in parsed["results"][0]["fixStatus"]
    assert "details" not in parsed["results"][0]["fixStatus"]
    assert "fixMetadata" not in parsed["results"][0]
    assert "fixQuality" not in parsed["results"][0]
    assert "reasoningSteps" not in parsed["results"][0]
