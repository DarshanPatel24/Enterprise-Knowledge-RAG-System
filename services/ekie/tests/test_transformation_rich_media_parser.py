from __future__ import annotations

from domain.transformation.parsers import ParserContext, default_registry


def test_rich_media_parser_is_registered_for_pdf() -> None:
    registry = default_registry()
    parser = registry.select(
        ParserContext(source_path="demo.pdf", extension="pdf", mime_type="application/pdf")
    )
    assert parser.parser_type == "rich_media"


def test_rich_media_parser_is_registered_for_docx() -> None:
    registry = default_registry()
    parser = registry.select(
        ParserContext(
            source_path="demo.docx",
            extension="docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    )
    assert parser.parser_type == "rich_media"


def test_rich_media_parser_is_registered_for_pptx() -> None:
    registry = default_registry()
    parser = registry.select(
        ParserContext(
            source_path="deck.pptx",
            extension="pptx",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
    )
    assert parser.parser_type == "rich_media"


def test_rich_media_parser_is_registered_for_images() -> None:
    registry = default_registry()
    parser = registry.select(
        ParserContext(source_path="scan.png", extension="png", mime_type="image/png")
    )
    assert parser.parser_type == "rich_media"
