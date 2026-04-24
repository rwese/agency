"""Markdown parser module.

This module provides parsing functionality for converting Markdown to HTML.
Supports standard Markdown and GitHub Flavored Markdown (GFM) extensions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar


class BlockType(Enum):
    """Enumeration of supported Markdown block types."""

    PARAGRAPH = auto()
    HEADING = auto()
    CODE_BLOCK = auto()
    BLOCKQUOTE = auto()
    UNORDERED_LIST = auto()
    ORDERED_LIST = auto()
    HORIZONTAL_RULE = auto()
    TABLE = auto()


@dataclass
class Block:
    """Represents a parsed Markdown block element."""

    block_type: BlockType
    content: str
    raw: str
    meta: dict | None = None


class MarkdownParser:
    """Parser for converting Markdown text to HTML.

    Supports:
    - Standard Markdown elements (headings, lists, links, images, code blocks)
    - GitHub Flavored Markdown (tables, task lists, strikethrough)
    - Syntax highlighting for code blocks

    Attributes:
        gfm_enabled: Whether to enable GFM extensions.
        code_highlighter: Optional code highlighter for syntax highlighting.
    """

    # Regex patterns for parsing
    HEADING_PATTERN: ClassVar[re.Pattern] = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    CODE_BLOCK_PATTERN: ClassVar[re.Pattern] = re.compile(r'^```(\w*)\n([\s\S]*?)```$', re.MULTILINE)
    BLOCKQUOTE_PATTERN: ClassVar[re.Pattern] = re.compile(r'^>\s*(.*)$', re.MULTILINE)
    UNORDERED_LIST_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[-*+]\s+(.+)$', re.MULTILINE)
    ORDERED_LIST_PATTERN: ClassVar[re.Pattern] = re.compile(r'^\d+\.\s+(.+)$', re.MULTILINE)
    HR_PATTERN: ClassVar[re.Pattern] = re.compile(r'^(-{3,}|\*{3,}|_{3,})$', re.MULTILINE)
    TABLE_ROW_PATTERN: ClassVar[re.Pattern] = re.compile(r'^\|(.+)\|$')
    TABLE_SEPARATOR_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[\s|:-]+$')
    INLINE_CODE_PATTERN: ClassVar[re.Pattern] = re.compile(r'`([^`]+)`')
    INLINE_LINK_PATTERN: ClassVar[re.Pattern] = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    INLINE_IMAGE_PATTERN: ClassVar[re.Pattern] = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    INLINE_BOLD_PATTERN: ClassVar[re.Pattern] = re.compile(r'\*\*([^*]+)\*\*')
    INLINE_ITALIC_PATTERN: ClassVar[re.Pattern] = re.compile(r'\*([^*]+)\*')

    def __init__(self, gfm_enabled: bool = True) -> None:
        """Initialize the Markdown parser.

        Args:
            gfm_enabled: Whether to enable GitHub Flavored Markdown extensions.
        """
        self.gfm_enabled = gfm_enabled
        self.code_highlighter: callable | None = None

    def parse(self, markdown: str) -> list[Block]:
        """Parse Markdown text into a list of blocks.

        Args:
            markdown: The Markdown text to parse.

        Returns:
            List of parsed Block objects.
        """
        blocks: list[Block] = []
        lines = markdown.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Skip empty lines but track them
            if not line.strip():
                i += 1
                continue

            # Check for code blocks (can span multiple lines)
            if line.startswith('```'):
                block, consumed = self._parse_code_block(lines[i:])
                if block:
                    blocks.append(block)
                    i += consumed
                    continue

            # Check for headings
            heading_match = self.HEADING_PATTERN.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2)
                blocks.append(Block(
                    block_type=BlockType.HEADING,
                    content=content,
                    raw=line,
                    meta={'level': level}
                ))
                i += 1
                continue

            # Check for horizontal rule
            if self.HR_PATTERN.match(line.strip()):
                blocks.append(Block(
                    block_type=BlockType.HORIZONTAL_RULE,
                    content='',
                    raw=line
                ))
                i += 1
                continue

            # Check for blockquote
            if line.startswith('>'):
                block, consumed = self._parse_blockquote(lines[i:])
                if block:
                    blocks.append(block)
                    i += consumed
                    continue

            # Check for table (GFM)
            if self.gfm_enabled and self._is_table_row(line):
                block, consumed = self._parse_table(lines[i:])
                if block:
                    blocks.append(block)
                    i += consumed
                    continue

            # Check for unordered list
            if line.strip().startswith(('- ', '* ', '+ ')):
                block, consumed = self._parse_unordered_list(lines[i:])
                if block:
                    blocks.append(block)
                    i += consumed
                    continue

            # Check for ordered list
            if self._is_ordered_list_item(line):
                block, consumed = self._parse_ordered_list(lines[i:])
                if block:
                    blocks.append(block)
                    i += consumed
                    continue

            # Default to paragraph
            block, consumed = self._parse_paragraph(lines[i:])
            if block:
                blocks.append(block)
            i += consumed

        return blocks

    def _parse_code_block(self, lines: list[str]) -> tuple[Block | None, int]:
        """Parse a fenced code block.

        Args:
            lines: Lines starting with the opening fence.

        Returns:
            Tuple of (Block, number of lines consumed).
        """
        if not lines or not lines[0].startswith('```'):
            return None, 0

        # Get language from fence (e.g., ```python)
        language = lines[0][3:].strip()

        content_lines: list[str] = []
        consumed = 1
        end_found = False

        for i in range(1, len(lines)):
            consumed += 1
            if lines[i].startswith('```'):
                end_found = True
                break
            content_lines.append(lines[i])

        if not end_found:
            return None, 0

        return Block(
            block_type=BlockType.CODE_BLOCK,
            content='\n'.join(content_lines),
            raw='\n'.join(lines[:consumed]),
            meta={'language': language}
        ), consumed

    def _parse_blockquote(self, lines: list[str]) -> tuple[Block | None, int]:
        """Parse a blockquote section.

        Args:
            lines: Lines starting with > marker.

        Returns:
            Tuple of (Block, number of lines consumed).
        """
        content_lines: list[str] = []
        consumed = 0

        for line in lines:
            if line.startswith('>'):
                content_lines.append(line[1:].strip())
                consumed += 1
            else:
                break

        return Block(
            block_type=BlockType.BLOCKQUOTE,
            content=' '.join(content_lines),
            raw='\n'.join(lines[:consumed])
        ), consumed

    def _parse_unordered_list(self, lines: list[str]) -> tuple[Block | None, int]:
        """Parse an unordered list section.

        Args:
            lines: Lines potentially containing list items.

        Returns:
            Tuple of (Block, number of lines consumed).
        """
        items: list[str] = []
        consumed = 0

        for line in lines:
            match = self.UNORDERED_LIST_PATTERN.match(line)
            if match:
                items.append(match.group(1))
                consumed += 1
            else:
                break

        if not items:
            return None, 0

        return Block(
            block_type=BlockType.UNORDERED_LIST,
            content='\n'.join(items),
            raw='\n'.join(lines[:consumed])
        ), consumed

    def _parse_ordered_list(self, lines: list[str]) -> tuple[Block | None, int]:
        """Parse an ordered list section.

        Args:
            lines: Lines potentially containing list items.

        Returns:
            Tuple of (Block, number of lines consumed).
        """
        items: list[str] = []
        consumed = 0

        for line in lines:
            match = self.ORDERED_LIST_PATTERN.match(line)
            if match:
                items.append(match.group(1))
                consumed += 1
            else:
                break

        if not items:
            return None, 0

        return Block(
            block_type=BlockType.ORDERED_LIST,
            content='\n'.join(items),
            raw='\n'.join(lines[:consumed])
        ), consumed

    def _parse_table(self, lines: list[str]) -> tuple[Block | None, int]:
        """Parse a GFM table section.

        Args:
            lines: Lines potentially containing table rows.

        Returns:
            Tuple of (Block, number of lines consumed).
        """
        rows: list[str] = []
        consumed = 0

        for line in lines:
            # Skip table separator row (|---|---|)
            if self.TABLE_SEPARATOR_PATTERN.match(line.strip()):
                consumed += 1
                continue

            if self.TABLE_ROW_PATTERN.match(line.strip()):
                # Extract cells from the row
                cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
                rows.append('|'.join(cells))
                consumed += 1
            else:
                break

        if len(rows) < 1:
            return None, 0

        return Block(
            block_type=BlockType.TABLE,
            content='\n'.join(rows),
            raw='\n'.join(lines[:consumed])
        ), consumed

    def _parse_paragraph(self, lines: list[str]) -> tuple[Block, int]:
        """Parse a paragraph section.

        Args:
            lines: Lines for the paragraph.

        Returns:
            Tuple of (Block, number of lines consumed).
        """
        content_lines: list[str] = []
        consumed = 0

        for line in lines:
            # End paragraph on empty line or special block
            if not line.strip():
                break
            if self.HEADING_PATTERN.match(line):
                break
            if line.startswith('```'):
                break
            if self.HR_PATTERN.match(line.strip()):
                break

            content_lines.append(line)
            consumed += 1

        return Block(
            block_type=BlockType.PARAGRAPH,
            content=' '.join(content_lines),
            raw='\n'.join(lines[:consumed])
        ), consumed

    def _is_table_row(self, line: str) -> bool:
        """Check if a line is a valid table row.

        Args:
            line: The line to check.

        Returns:
            True if the line is a valid table row.
        """
        stripped = line.strip()
        return bool(self.TABLE_ROW_PATTERN.match(stripped))

    def _is_ordered_list_item(self, line: str) -> bool:
        """Check if a line is an ordered list item.

        Args:
            line: The line to check.

        Returns:
            True if the line is an ordered list item.
        """
        return bool(self.ORDERED_LIST_PATTERN.match(line))
