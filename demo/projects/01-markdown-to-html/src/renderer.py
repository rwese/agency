"""HTML renderer module.

This module provides rendering functionality for converting parsed Markdown
blocks to HTML output with syntax highlighting support.
"""

from __future__ import annotations

from html import escape
from typing import ClassVar

from src.parser import Block, BlockType, MarkdownParser


class HTMLRenderer:
    """Renders parsed Markdown blocks as HTML.

    Supports:
    - All standard Markdown block types
    - Inline formatting (bold, italic, code, links, images)
    - Syntax highlighting for code blocks
    - Standalone HTML output with embedded CSS

    Attributes:
        parser: The MarkdownParser instance for parsing inline elements.
        standalone: Whether to generate standalone HTML with embedded CSS.
        css_template: Optional CSS template for standalone output.
    """

    DEFAULT_CSS: ClassVar[str] = """
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        line-height: 1.6;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        color: #333;
    }
    h1, h2, h3, h4, h5, h6 {
        margin-top: 24px;
        margin-bottom: 16px;
        font-weight: 600;
        line-height: 1.25;
    }
    h1 { font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
    h2 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
    h3 { font-size: 1.25em; }
    code {
        background-color: rgba(27, 31, 35, 0.05);
        padding: 0.2em 0.4em;
        border-radius: 3px;
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        font-size: 85%;
    }
    pre {
        background-color: #f6f8fa;
        padding: 16px;
        border-radius: 6px;
        overflow-x: auto;
    }
    pre code {
        background: none;
        padding: 0;
    }
    blockquote {
        border-left: 4px solid #dfe2e5;
        padding-left: 16px;
        margin: 0;
        color: #6a737d;
    }
    a { color: #0366d6; text-decoration: none; }
    a:hover { text-decoration: underline; }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 16px 0;
    }
    th, td {
        border: 1px solid #dfe2e5;
        padding: 8px 13px;
    }
    th { background-color: #f6f8fa; }
    ul, ol { padding-left: 2em; }
    li { margin: 4px 0; }
    hr { border: none; border-top: 1px solid #dfe2e5; margin: 24px 0; }
    img { max-width: 100%; }
    """

    def __init__(
        self,
        parser: MarkdownParser | None = None,
        standalone: bool = False,
        css_template: str | None = None
    ) -> None:
        """Initialize the HTML renderer.

        Args:
            parser: MarkdownParser instance for inline parsing.
            standalone: Whether to generate standalone HTML.
            css_template: Custom CSS for standalone output.
        """
        self.parser = parser or MarkdownParser()
        self.standalone = standalone
        self.css_template = css_template or self.DEFAULT_CSS

    def render(self, blocks: list[Block]) -> str:
        """Render parsed blocks to HTML.

        Args:
            blocks: List of parsed Block objects.

        Returns:
            HTML string.
        """
        html_parts: list[str] = []

        for block in blocks:
            html_parts.append(self._render_block(block))

        return '\n'.join(html_parts)

    def _render_block(self, block: Block) -> str:
        """Render a single block to HTML.

        Args:
            block: The Block to render.

        Returns:
            HTML string for the block.
        """
        handlers = {
            BlockType.HEADING: self._render_heading,
            BlockType.PARAGRAPH: self._render_paragraph,
            BlockType.CODE_BLOCK: self._render_code_block,
            BlockType.BLOCKQUOTE: self._render_blockquote,
            BlockType.UNORDERED_LIST: self._render_unordered_list,
            BlockType.ORDERED_LIST: self._render_ordered_list,
            BlockType.HORIZONTAL_RULE: self._render_horizontal_rule,
            BlockType.TABLE: self._render_table,
        }

        handler = handlers.get(block.block_type)
        if handler:
            return handler(block)
        return ''

    def _render_heading(self, block: Block) -> str:
        """Render a heading block.

        Args:
            block: The heading block.

        Returns:
            HTML for the heading.
        """
        level = block.meta.get('level', 1) if block.meta else 1
        content = escape(block.content)
        content = self._render_inline(content)
        return f'<h{level}>{content}</h{level}>'

    def _render_paragraph(self, block: Block) -> str:
        """Render a paragraph block.

        Args:
            block: The paragraph block.

        Returns:
            HTML for the paragraph.
        """
        content = escape(block.content)
        content = self._render_inline(content)
        return f'<p>{content}</p>'

    def _render_code_block(self, block: Block) -> str:
        """Render a code block with optional syntax highlighting.

        Args:
            block: The code block.

        Returns:
            HTML for the code block.
        """
        language = block.meta.get('language', '') if block.meta else ''
        code = escape(block.content)

        # Use syntax highlighting if available
        if self.parser.code_highlighter and language:
            try:
                highlighted = self.parser.code_highlighter(code, language)
                return f'<pre><code class="language-{escape(language)}">{highlighted}</code></pre>'
            except Exception:
                pass

        return f'<pre><code class="language-{escape(language)}">{code}</code></pre>'

    def _render_blockquote(self, block: Block) -> str:
        """Render a blockquote.

        Args:
            block: The blockquote block.

        Returns:
            HTML for the blockquote.
        """
        content = escape(block.content)
        content = self._render_inline(content)
        return f'<blockquote>{content}</blockquote>'

    def _render_unordered_list(self, block: Block) -> str:
        """Render an unordered list.

        Args:
            block: The list block.

        Returns:
            HTML for the unordered list.
        """
        items = [self._render_inline(escape(item)) for item in block.content.split('\n')]
        list_items = '\n'.join(f'<li>{item}</li>' for item in items)
        return f'<ul>\n{list_items}\n</ul>'

    def _render_ordered_list(self, block: Block) -> str:
        """Render an ordered list.

        Args:
            block: The list block.

        Returns:
            HTML for the ordered list.
        """
        items = [self._render_inline(escape(item)) for item in block.content.split('\n')]
        list_items = '\n'.join(f'<li>{item}</li>' for item in items)
        return f'<ol>\n{list_items}\n</ol>'

    def _render_horizontal_rule(self, block: Block) -> str:
        """Render a horizontal rule.

        Args:
            block: The horizontal rule block.

        Returns:
            HTML for the horizontal rule.
        """
        return '<hr>'

    def _render_table(self, block: Block) -> str:
        """Render a table.

        Args:
            block: The table block.

        Returns:
            HTML for the table.
        """
        rows = block.content.split('\n')
        if not rows:
            return ''

        # First row is header
        headers = [self._render_inline(cell) for cell in rows[0].split('|') if cell]

        # Build table
        html = '<table>\n<thead>\n<tr>\n'
        html += ''.join(f'<th>{h}</th>' for h in headers)
        html += '\n</tr>\n</thead>\n<tbody>\n'

        # Data rows
        for row in rows[1:]:
            cells = [self._render_inline(cell) for cell in row.split('|') if cell]
            html += '<tr>\n'
            html += ''.join(f'<td>{c}</td>' for c in cells)
            html += '\n</tr>\n'

        html += '</tbody>\n</table>'
        return html

    def _render_inline(self, text: str) -> str:
        """Render inline Markdown elements.

        Args:
            text: The text to render.

        Returns:
            HTML with inline elements rendered.
        """
        # Apply patterns in order
        text = self.parser.INLINE_IMAGE_PATTERN.sub(
            r'<img src="\2" alt="\1">', text
        )
        text = self.parser.INLINE_LINK_PATTERN.sub(
            r'<a href="\2">\1</a>', text
        )
        text = self.parser.INLINE_BOLD_PATTERN.sub(
            r'<strong>\1</strong>', text
        )
        text = self.parser.INLINE_ITALIC_PATTERN.sub(
            r'<em>\1</em>', text
        )
        text = self.parser.INLINE_CODE_PATTERN.sub(
            r'<code>\1</code>', text
        )

        return text

    def render_standalone(self, blocks: list[Block], title: str = "Document") -> str:
        """Render blocks to standalone HTML with embedded CSS.

        Args:
            blocks: List of parsed Block objects.
            title: Page title for the HTML document.

        Returns:
            Complete HTML document string.
        """
        content = self.render(blocks)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    <style>
{self.css_template}
    </style>
</head>
<body>
{content}
</body>
</html>"""
        return html
