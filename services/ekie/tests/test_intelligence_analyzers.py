"""Unit tests for the individual document intelligence analyzers."""

from domain.intelligence import (
    DocumentCategory,
    DocumentComplexity,
    IntelligencePolicy,
    IntelligenceReportBuilder,
    SensitiveContentType,
    build_analyzed_document,
    default_analyzers,
    parse_markdown,
)
from domain.intelligence.analyzers import (
    ClassificationAnalyzer,
    LanguageAnalyzer,
    QualityAnalyzer,
    SensitiveContentAnalyzer,
    StructureAnalyzer,
    TableAnalyzer,
)


def _run(analyzers: list, text: str, policy: IntelligencePolicy | None = None):
    policy = policy or IntelligencePolicy()
    analyzed = build_analyzed_document(parse_markdown(text))
    builder = IntelligenceReportBuilder(language=policy.default_language)
    for analyzer in analyzers:
        analyzer.analyze(analyzed, builder, policy)
    return builder


def test_structure_computes_sections_and_topic() -> None:
    text = "# Title\n\nBody text one two three.\n\n## Sub\n\nmore words here now.\n"
    builder = _run([StructureAnalyzer()], text)
    assert builder.primary_topic == "Title"
    assert len(builder.sections) == 2
    assert builder.token_count > 0
    assert builder.complexity is DocumentComplexity.LOW


def test_table_analyzer_flags_numeric_and_dates() -> None:
    text = (
        "# T\n\n| Part | Qty | Date |\n| --- | --- | --- |\n"
        "| ABC-1 | 12 | 2024-01-02 |\n"
    )
    builder = _run([StructureAnalyzer(), TableAnalyzer()], text)
    assert len(builder.tables) == 1
    table = builder.tables[0]
    assert table.rows == 1
    assert table.columns == 3
    assert table.contains_numeric is True
    assert table.contains_dates is True
    assert table.contains_ids is True


def test_language_prefers_front_matter() -> None:
    text = "---\nlanguage: de\n---\n\n# Titel\n\nDer text ist hier.\n"
    builder = _run([LanguageAnalyzer()], text)
    assert builder.language == "de"


def test_classification_detects_policy() -> None:
    text = "# Data Retention Policy\n\nThis policy governs retention of records.\n"
    builder = _run([ClassificationAnalyzer()], text)
    assert builder.classification is DocumentCategory.POLICY


def test_sensitive_content_flags_email_and_secret() -> None:
    text = (
        "# Contact\n\nEmail admin@example.com for access.\n\n"
        "api_key: ABCD1234SECRETVALUE\n"
    )
    builder = _run([SensitiveContentAnalyzer()], text)
    found = {finding.finding_type for finding in builder.sensitive_findings}
    assert SensitiveContentType.EMAIL_ADDRESS in found
    assert SensitiveContentType.API_KEY in found


def test_sensitive_content_disabled_by_policy() -> None:
    policy = IntelligencePolicy(detect_sensitive_content=False)
    text = "Email admin@example.com now.\n"
    builder = _run([SensitiveContentAnalyzer()], text, policy)
    assert builder.sensitive_findings == []


def test_quality_score_has_components() -> None:
    text = "# Title\n\nSome content here for scoring.\n"
    builder = _run(default_analyzers(), text)
    assert builder.quality is not None
    assert 0 <= builder.quality.overall <= 100
    assert set(builder.quality.components) == {
        "structure",
        "content",
        "tables",
        "images",
    }


def test_quality_penalizes_ragged_tables() -> None:
    ragged = (
        "# T\n\n| A | B | C |\n| --- | --- | --- |\n| 1 | 2 |\n"
    )
    builder = _run([StructureAnalyzer(), TableAnalyzer(), QualityAnalyzer()], ragged)
    assert builder.quality is not None
    assert builder.quality.components["tables"] < 100
