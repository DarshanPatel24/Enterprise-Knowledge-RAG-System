"""Tests for transformation parsers and the parser registry.

EKIE ingests Markdown produced upstream by the EKDC converter; only Markdown
and a defensive plain-text fallback are supported here.
"""

import pytest

from domain.transformation.parsers import (
    MarkdownParser,
    ParserContext,
    PlainTextParser,
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


def test_markdown_parser_passthrough() -> None:
    result = MarkdownParser().parse(b"# Title\n\ntext", _ctx("readme.md"))
    assert result.body == "# Title\n\ntext"
    assert result.metadata.title == "readme"


def test_registry_selects_markdown_by_extension() -> None:
    registry = default_registry()
    parser = registry.select(_ctx("guide.md"))
    assert isinstance(parser, MarkdownParser)


def test_registry_selects_plain_text_by_extension() -> None:
    registry = default_registry()
    parser = registry.select(_ctx("notes.txt"))
    assert isinstance(parser, PlainTextParser)


def test_registry_selects_by_mime_when_extension_unknown() -> None:
    registry = default_registry()
    parser = registry.select(ParserContext("f.unknown", "unknown", "text/markdown"))
    assert isinstance(parser, MarkdownParser)


def test_registry_raises_for_unsupported_format() -> None:
    registry = default_registry()
    with pytest.raises(UnsupportedFormatError):
        registry.select(_ctx("scan.pdf"))
