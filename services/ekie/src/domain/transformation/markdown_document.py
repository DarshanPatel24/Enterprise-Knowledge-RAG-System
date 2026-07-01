"""Canonical Markdown document model with YAML front matter (handbook 7.10)."""

from __future__ import annotations

from dataclasses import dataclass


def _yaml_scalar(value: str) -> str:
    """Render ``value`` as a deterministic, safe YAML scalar."""
    needs_quoting = (
        value == ""
        or value != value.strip()
        or any(ch in value for ch in ':#"\n')
        or value[0] in "!&*?|>%@`[]{},"
    )
    if needs_quoting:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    return value


@dataclass(frozen=True)
class FrontMatter:
    """Structured YAML front matter for a canonical Markdown asset."""

    document_id: str
    repository_id: str
    version: int
    source_type: str
    source_hash: str
    language: str
    title: str | None = None
    author: str | None = None
    created_at: str | None = None

    def _ordered_items(self) -> list[tuple[str, str]]:
        items: list[tuple[str, str]] = [
            ("document_id", self.document_id),
            ("repository_id", self.repository_id),
            ("version", str(self.version)),
            ("source_type", self.source_type),
            ("source_hash", self.source_hash),
            ("language", self.language),
        ]
        if self.title is not None:
            items.append(("title", self.title))
        if self.author is not None:
            items.append(("author", self.author))
        if self.created_at is not None:
            items.append(("created_at", self.created_at))
        return items

    def render(self) -> str:
        """Render the front matter as a deterministic YAML block."""
        lines = ["---"]
        for key, value in self._ordered_items():
            lines.append(f"{key}: {_yaml_scalar(value)}")
        lines.append("---")
        return "\n".join(lines)

    def required_keys(self) -> frozenset[str]:
        """Return the mandatory front matter keys for validation."""
        return frozenset(
            {"document_id", "repository_id", "version", "source_type", "source_hash", "language"}
        )


@dataclass(frozen=True)
class MarkdownDocument:
    """A canonical Markdown document composed of front matter and body."""

    body: str
    front_matter: FrontMatter | None = None

    def render(self) -> str:
        """Render the complete canonical Markdown document as text."""
        body = self.body.strip("\n")
        if self.front_matter is None:
            return f"{body}\n" if body else ""
        if not body:
            return f"{self.front_matter.render()}\n"
        return f"{self.front_matter.render()}\n\n{body}\n"

    def render_bytes(self) -> bytes:
        """Render the document to deterministic UTF-8 bytes for storage."""
        return self.render().encode("utf-8")
