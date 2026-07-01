"""Unit tests for the canonical Markdown AST parser and section analysis."""

from domain.intelligence import (
    BlockType,
    build_analyzed_document,
    parse_markdown,
)

_SAMPLE = """---
title: Pump Maintenance
language: en
---

# Overview

Intro paragraph with some words here.

## Safety

> Warning: disconnect power before service.

### Steps

1. Stop the pump.
2. Drain the reservoir.

## Specifications

| Part | Torque | Date |
| --- | --- | --- |
| Bolt A | 45 | 2024-01-02 |
| Bolt B | 60 | 2024-03-11 |

![Diagram of pump](images/pump.png)

```python
def start():
    return True
```
"""


def test_parse_front_matter_and_block_types() -> None:
    parsed = parse_markdown(_SAMPLE)

    assert parsed.front_matter["title"] == "Pump Maintenance"
    assert parsed.front_matter["language"] == "en"

    types = [block.block_type for block in parsed.blocks]
    assert BlockType.HEADING in types
    assert BlockType.TABLE in types
    assert BlockType.CODE in types
    assert BlockType.IMAGE in types
    assert BlockType.NOTE in types


def test_table_and_code_details() -> None:
    parsed = parse_markdown(_SAMPLE)

    table = next(b for b in parsed.blocks if b.block_type is BlockType.TABLE)
    assert table.table_rows[0] == ["Part", "Torque", "Date"]
    assert len(table.table_rows) == 3

    code = next(b for b in parsed.blocks if b.block_type is BlockType.CODE)
    assert code.language == "python"
    assert "def start" in code.text

    image = next(b for b in parsed.blocks if b.block_type is BlockType.IMAGE)
    assert image.text == "Diagram of pump"
    assert image.language == "images/pump.png"


def test_section_tree_is_hierarchical() -> None:
    analyzed = build_analyzed_document(parse_markdown(_SAMPLE))

    titles = [section.title for section in analyzed.sections]
    assert titles == ["Overview", "Safety", "Steps", "Specifications"]

    overview = analyzed.sections[0]
    safety = analyzed.sections[1]
    steps = analyzed.sections[2]
    assert overview.parent_id is None
    assert safety.parent_id == overview.section_id
    assert steps.parent_id == safety.section_id
    assert safety.section_id in overview.child_ids


def test_blocks_assigned_to_sections() -> None:
    analyzed = build_analyzed_document(parse_markdown(_SAMPLE))
    spec_section = next(s for s in analyzed.sections if s.title == "Specifications")
    blocks = analyzed.blocks_for_section(spec_section.section_id)
    assert any(b.block_type is BlockType.TABLE for b in blocks)
    assert any(b.block_type is BlockType.IMAGE for b in blocks)
