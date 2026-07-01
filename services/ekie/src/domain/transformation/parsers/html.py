"""HTML parser producing canonical Markdown (pure Python stdlib html.parser)."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import PurePosixPath
from typing import ClassVar

from domain.transformation.parsers.base import (
    DocumentParser,
    ExtractedMetadata,
    ParsedContent,
    ParserContext,
)

_HEADINGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}
_SKIP_CONTENT = frozenset({"script", "style", "head"})
_WHITESPACE = re.compile(r"[ \t]+")


class _MarkdownHtmlParser(HTMLParser):
    """Streaming HTML-to-Markdown converter with deterministic output."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self.title: str | None = None
        self.language: str | None = None
        self._buffer: list[str] = []
        self._skip_depth = 0
        self._in_title = False
        self._list_ordered: list[bool] = []
        self._list_index: list[int] = []
        self._table_row: list[str] | None = None
        self._table_rows: list[list[str]] = []
        self._in_table = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "html" and attributes.get("lang"):
            self.language = attributes["lang"]
        if tag in _SKIP_CONTENT:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
            return
        if tag in _HEADINGS or tag in {"p", "div"}:
            self._flush_paragraph()
        elif tag in {"ul", "ol"}:
            self._flush_paragraph()
            self._list_ordered.append(tag == "ol")
            self._list_index.append(0)
        elif tag == "li":
            self._flush_paragraph()
        elif tag in {"strong", "b"}:
            self._buffer.append("**")
        elif tag in {"em", "i"}:
            self._buffer.append("*")
        elif tag == "code":
            self._buffer.append("`")
        elif tag == "br":
            self._buffer.append("  \n")
        elif tag == "a":
            self._buffer.append("[")
        elif tag == "img":
            alt = attributes.get("alt") or ""
            src = attributes.get("src") or ""
            self._buffer.append(f"![{alt}]({src})")
        elif tag == "table":
            self._flush_paragraph()
            self._in_table = True
            self._table_rows = []
        elif tag == "tr" and self._in_table:
            self._table_row = []
        elif tag in {"td", "th"} and self._in_table:
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_CONTENT:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag == "title":
            self._in_title = False
            self.title = self._collapse("".join(self._buffer)) or self.title
            self._buffer = []
            return
        if tag in _HEADINGS:
            text = self._collapse("".join(self._buffer))
            if text:
                self.blocks.append(f"{_HEADINGS[tag]} {text}")
            self._buffer = []
        elif tag in {"p", "div"}:
            self._flush_paragraph()
        elif tag in {"ul", "ol"}:
            if self._list_ordered:
                self._list_ordered.pop()
                self._list_index.pop()
        elif tag == "li":
            text = self._collapse("".join(self._buffer))
            self._buffer = []
            if text:
                if self._list_ordered and self._list_ordered[-1]:
                    self._list_index[-1] += 1
                    self.blocks.append(f"{self._list_index[-1]}. {text}")
                else:
                    self.blocks.append(f"- {text}")
        elif tag in {"strong", "b"}:
            self._buffer.append("**")
        elif tag in {"em", "i"}:
            self._buffer.append("*")
        elif tag == "code":
            self._buffer.append("`")
        elif tag == "a":
            self._buffer.append("]")
        elif tag in {"td", "th"} and self._in_table and self._table_row is not None:
            self._table_row.append(self._collapse("".join(self._buffer)))
            self._buffer = []
        elif tag == "tr" and self._in_table and self._table_row is not None:
            self._table_rows.append(self._table_row)
            self._table_row = None
        elif tag == "table":
            self._emit_table()
            self._in_table = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._buffer.append(data)
            return
        if self._skip_depth:
            return
        self._buffer.append(data)

    def _flush_paragraph(self) -> None:
        if self._in_table:
            return
        text = self._collapse("".join(self._buffer))
        self._buffer = []
        if text:
            self.blocks.append(text)

    def _emit_table(self) -> None:
        if not self._table_rows:
            return
        width = max(len(row) for row in self._table_rows)
        header = self._table_rows[0] + [""] * (width - len(self._table_rows[0]))
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(["---"] * width) + " |",
        ]
        for row in self._table_rows[1:]:
            padded = row + [""] * (width - len(row))
            lines.append("| " + " | ".join(padded) + " |")
        self.blocks.append("\n".join(lines))
        self._table_rows = []

    @staticmethod
    def _collapse(text: str) -> str:
        return _WHITESPACE.sub(" ", text.replace("\n", " ")).strip()


class HtmlParser(DocumentParser):
    """Parser converting HTML into canonical Markdown (handbook 7.6)."""

    parser_type: ClassVar[str] = "html"
    parser_version: ClassVar[str] = "1.0"
    supported_extensions: ClassVar[frozenset[str]] = frozenset({"html", "htm", "xhtml"})
    supported_mime_types: ClassVar[frozenset[str]] = frozenset({"text/html"})

    def parse(self, data: bytes, context: ParserContext) -> ParsedContent:
        """Convert HTML markup into Markdown blocks with extracted metadata."""
        converter = _MarkdownHtmlParser()
        converter.feed(self.decode(data))
        converter.close()
        converter._flush_paragraph()
        body = "\n\n".join(block for block in converter.blocks if block)
        title = converter.title or PurePosixPath(context.source_path).stem
        return ParsedContent(
            body=body,
            metadata=ExtractedMetadata(title=title, language=converter.language),
        )
