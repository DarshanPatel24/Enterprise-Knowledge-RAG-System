"""Tests for transformation parsers and the parser registry."""

import pytest

from domain.transformation.parsers import (
    CsvParser,
    HtmlParser,
    MarkdownParser,
    ParserContext,
    PlainTextParser,
    SourceCodeParser,
    UnsupportedFormatError,
    default_registry,
)


def _ctx(path: str, mime: str | None = None) -> ParserContext:
    extension = path.rsplit(".", 1)[-1].lower()
    return ParserContext(source_path=path, extension=extension, mime_type=mime)


def test_plain_text_parser_returns_text_and_title() -> None:
    result = PlainTextParser().parse(b"hello world", _ctx("docs/note.txt"))
    assert result.body == "hello world"
    assert result.metadata.title == "note"


def test_source_code_parser_wraps_in_fenced_block() -> None:
    result = SourceCodeParser().parse(b"print('hi')\n", _ctx("app/main.py"))
    assert result.body == "```python\nprint('hi')\n```"


def test_markdown_parser_passthrough() -> None:
    result = MarkdownParser().parse(b"# Title\n\ntext", _ctx("readme.md"))
    assert result.body == "# Title\n\ntext"


def test_csv_parser_builds_markdown_table() -> None:
    data = b"name,role\nAda,Engineer\nGrace,Admiral\n"
    result = CsvParser().parse(data, _ctx("people.csv"))
    lines = result.body.splitlines()
    assert lines[0] == "| name | role |"
    assert lines[1] == "| --- | --- |"
    assert lines[2] == "| Ada | Engineer |"


def test_csv_parser_escapes_pipe_characters() -> None:
    result = CsvParser().parse(b"a|b,c\n1,2\n", _ctx("x.csv"))
    assert "a\\|b" in result.body


def test_html_parser_extracts_headings_and_metadata() -> None:
    html = (
        b"<html lang='en'><head><title>Doc</title></head>"
        b"<body><h1>Heading</h1><p>Para <strong>bold</strong></p>"
        b"<ul><li>one</li><li>two</li></ul></body></html>"
    )
    result = HtmlParser().parse(html, _ctx("page.html"))
    assert "# Heading" in result.body
    assert "Para **bold**" in result.body
    assert "- one" in result.body
    assert result.metadata.title == "Doc"
    assert result.metadata.language == "en"


def test_html_parser_converts_tables_and_images() -> None:
    html = (
        b"<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
        b"<img src='diagram.png' alt='Diagram'>"
    )
    result = HtmlParser().parse(html, _ctx("t.html"))
    assert "| A | B |" in result.body
    assert "| 1 | 2 |" in result.body
    assert "![Diagram](diagram.png)" in result.body


def test_registry_selects_by_extension() -> None:
    registry = default_registry()
    parser = registry.select(_ctx("data.csv"))
    assert isinstance(parser, CsvParser)


def test_registry_selects_by_mime_when_extension_unknown() -> None:
    registry = default_registry()
    parser = registry.select(ParserContext("f.unknown", "unknown", "text/html"))
    assert isinstance(parser, HtmlParser)


def test_registry_raises_for_unsupported_format() -> None:
    registry = default_registry()
    with pytest.raises(UnsupportedFormatError):
        registry.select(_ctx("archive.zip"))
