"""Deterministic text normalization engine (handbook 7.8).

Normalization guarantees that identical source content yields identical
Markdown regardless of incidental encoding, whitespace, or control-character
differences in the source document.
"""

from __future__ import annotations

import unicodedata

# C0/C1 control characters that must be stripped, excluding tab and newline.
_ALLOWED_CONTROL = {"\n", "\t"}


def normalize_text(
    text: str,
    *,
    normalize_unicode: bool = True,
    collapse_blank_lines: bool = True,
) -> str:
    """Return a normalized, deterministic representation of ``text``.

    Applies Unicode NFC normalization, converts all newline conventions to
    ``\\n``, removes hidden control characters, trims trailing whitespace per
    line, optionally collapses consecutive blank lines, and ensures a single
    trailing newline.
    """
    if normalize_unicode:
        text = unicodedata.normalize("NFC", text)

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _strip_control_characters(text)

    lines = [line.rstrip() for line in text.split("\n")]
    if collapse_blank_lines:
        lines = _collapse_blank_lines(lines)

    body = "\n".join(lines).strip("\n")
    return f"{body}\n" if body else ""


def _strip_control_characters(text: str) -> str:
    """Remove control characters except tab and newline."""
    return "".join(
        char
        for char in text
        if char in _ALLOWED_CONTROL or unicodedata.category(char)[0] != "C"
    )


def _collapse_blank_lines(lines: list[str]) -> list[str]:
    """Collapse runs of blank lines into a single blank line."""
    result: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue
        result.append(line)
        previous_blank = is_blank
    return result
