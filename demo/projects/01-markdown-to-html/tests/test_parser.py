"""Tests for the Markdown parser module.

Test cases from README.md:
- TC01: Parse heading - H1-H6 rendered correctly
- TC02: Parse lists - Ordered/unordered lists
- TC03: Parse code block - Syntax highlighting applied
- TC04: Parse table - Table with header and rows
- TC05: Parse link/image - Links work, images show
"""

from __future__ import annotations

import pytest

from src.parser import Block, BlockType, MarkdownParser
from src.renderer import HTMLRenderer


class TestMarkdownParser:
    """Test cases for the MarkdownParser class."""

    @pytest.fixture
    def parser(self) -> MarkdownParser:
        """Create a parser instance for testing."""
        return MarkdownParser(gfm_enabled=True)

    @pytest.fixture
    def parser_no_gfm(self) -> MarkdownParser:
        """Create a parser instance without GFM support."""
        return MarkdownParser(gfm_enabled=False)

    # TC01: Parse headings
    @pytest.mark.parametrize("level,markdown,expected_content", [
        (1, "# Heading 1", "Heading 1"),
        (2, "## Heading 2", "Heading 2"),
        (3, "### Heading 3", "Heading 3"),
        (4, "#### Heading 4", "Heading 4"),
        (5, "##### Heading 5", "Heading 5"),
        (6, "###### Heading 6", "Heading 6"),
    ])
    def test_parse_heading(
        self,
        parser: MarkdownParser,
        level: int,
        markdown: str,
        expected_content: str
    ) -> None:
        """Test that all heading levels are parsed correctly."""
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.HEADING
        assert blocks[0].content == expected_content
        assert blocks[0].meta['level'] == level

    def test_parse_multiple_headings(self, parser: MarkdownParser) -> None:
        """Test parsing multiple headings in sequence."""
        markdown = """# Heading 1
## Heading 2
### Heading 3"""
        blocks = parser.parse(markdown)

        assert len(blocks) == 3
        assert all(b.block_type == BlockType.HEADING for b in blocks)
        assert blocks[0].meta['level'] == 1
        assert blocks[1].meta['level'] == 2
        assert blocks[2].meta['level'] == 3

    # TC02: Parse lists
    def test_parse_unordered_list(self, parser: MarkdownParser) -> None:
        """Test parsing unordered lists."""
        markdown = """- Item 1
- Item 2
- Item 3"""
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.UNORDERED_LIST
        assert "Item 1" in blocks[0].content
        assert "Item 2" in blocks[0].content
        assert "Item 3" in blocks[0].content

    def test_parse_unordered_list_with_asterisk(self, parser: MarkdownParser) -> None:
        """Test parsing unordered lists with asterisk marker."""
        markdown = """* First item
* Second item"""
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.UNORDERED_LIST

    def test_parse_unordered_list_with_plus(self, parser: MarkdownParser) -> None:
        """Test parsing unordered lists with plus marker."""
        markdown = """+ Item A
+ Item B"""
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.UNORDERED_LIST

    def test_parse_ordered_list(self, parser: MarkdownParser) -> None:
        """Test parsing ordered lists."""
        markdown = """1. First
2. Second
3. Third"""
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.ORDERED_LIST
        assert "First" in blocks[0].content
        assert "Second" in blocks[0].content
        assert "Third" in blocks[0].content

    def test_parse_ordered_list_starting_nonzero(self, parser: MarkdownParser) -> None:
        """Test parsing ordered lists starting with non-zero."""
        markdown = """5. Fifth item
6. Sixth item"""
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.ORDERED_LIST

    # TC03: Parse code blocks
    def test_parse_code_block(self, parser: MarkdownParser) -> None:
        """Test parsing fenced code blocks."""
        markdown = """```python
def hello():
    print("Hello, World!")
```"""
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.CODE_BLOCK
        assert blocks[0].meta['language'] == 'python'
        assert 'def hello' in blocks[0].content
        assert 'print' in blocks[0].content

    def test_parse_code_block_no_language(self, parser: MarkdownParser) -> None:
        """Test parsing code blocks without language specification."""
        markdown = """```
some code
more code
```"""
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.CODE_BLOCK
        assert blocks[0].meta['language'] == ''

    def test_parse_code_block_different_languages(self, parser: MarkdownParser) -> None:
        """Test parsing code blocks with different languages."""
        markdown = """```javascript
const x = 1;
```

```rust
let x = 1;
```

```go
x := 1
```"""
        blocks = parser.parse(markdown)

        assert len(blocks) == 3
        assert blocks[0].meta['language'] == 'javascript'
        assert blocks[1].meta['language'] == 'rust'
        assert blocks[2].meta['language'] == 'go'

    # TC04: Parse tables
    def test_parse_table(self, parser: MarkdownParser) -> None:
        """Test parsing GFM tables."""
        markdown = """| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |"""
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.TABLE
        assert "Header 1" in blocks[0].content
        assert "Cell 1" in blocks[0].content
        assert "Cell 6" in blocks[0].content

    def test_parse_table_single_row(self, parser: MarkdownParser) -> None:
        """Test parsing tables with just header row."""
        markdown = """| Name | Value |
|----|----|
| Foo | Bar |"""
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.TABLE

    def test_parse_table_no_gfm(self, parser_no_gfm: MarkdownParser) -> None:
        """Test that tables are not parsed when GFM is disabled."""
        markdown = """| Header |
|-------|
| Cell  |"""
        blocks = parser_no_gfm.parse(markdown)

        # Should be parsed as paragraph, not table
        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.PARAGRAPH

    # TC05: Parse links and images
    def test_parse_paragraph_with_links(self, parser: MarkdownParser) -> None:
        """Test parsing paragraphs containing links."""
        markdown = "This is a [link](https://example.com) in text."
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.PARAGRAPH
        assert "[link](https://example.com)" in blocks[0].content

    def test_parse_paragraph_with_images(self, parser: MarkdownParser) -> None:
        """Test parsing paragraphs containing images."""
        markdown = "Here's an ![image](image.png) in text."
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.PARAGRAPH
        assert "![image](image.png)" in blocks[0].content

    # Additional test cases
    def test_parse_horizontal_rule_dashes(self, parser: MarkdownParser) -> None:
        """Test parsing horizontal rules with dashes."""
        markdown = "Some text\n\n---\n\nMore text"
        blocks = parser.parse(markdown)

        hr_blocks = [b for b in blocks if b.block_type == BlockType.HORIZONTAL_RULE]
        assert len(hr_blocks) == 1

    def test_parse_horizontal_rule_asterisks(self, parser: MarkdownParser) -> None:
        """Test parsing horizontal rules with asterisks."""
        markdown = "Text\n\n***\n\nText"
        blocks = parser.parse(markdown)

        hr_blocks = [b for b in blocks if b.block_type == BlockType.HORIZONTAL_RULE]
        assert len(hr_blocks) == 1

    def test_parse_blockquote(self, parser: MarkdownParser) -> None:
        """Test parsing blockquotes."""
        markdown = """> This is a quote
> with multiple lines"""
        blocks = parser.parse(markdown)

        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.BLOCKQUOTE
        assert "This is a quote" in blocks[0].content

    def test_parse_empty_input(self, parser: MarkdownParser) -> None:
        """Test parsing empty input."""
        blocks = parser.parse("")
        assert blocks == []

    def test_parse_whitespace_only(self, parser: MarkdownParser) -> None:
        """Test parsing whitespace-only input."""
        blocks = parser.parse("   \n\n   \n")
        assert blocks == []

    def test_parse_mixed_content(self, parser: MarkdownParser) -> None:
        """Test parsing mixed Markdown content."""
        markdown = """# Title

Some paragraph text with [a link](url).

- List item 1
- List item 2

```python
code block
```

> A quote

| Table | Header |
|-------|--------|
| Cell  | Value  |"""
        blocks = parser.parse(markdown)

        # Should have: heading, paragraph, unordered list, code block, blockquote, table
        assert len(blocks) == 6
        assert blocks[0].block_type == BlockType.HEADING
        assert blocks[1].block_type == BlockType.PARAGRAPH
        assert blocks[2].block_type == BlockType.UNORDERED_LIST
        assert blocks[3].block_type == BlockType.CODE_BLOCK
        assert blocks[4].block_type == BlockType.BLOCKQUOTE
        assert blocks[5].block_type == BlockType.TABLE


class TestHTMLRenderer:
    """Test cases for the HTMLRenderer class."""

    @pytest.fixture
    def renderer(self) -> HTMLRenderer:
        """Create a renderer instance for testing."""
        parser = MarkdownParser(gfm_enabled=True)
        return HTMLRenderer(parser=parser)

    @pytest.fixture
    def renderer_standalone(self) -> HTMLRenderer:
        """Create a standalone renderer instance."""
        parser = MarkdownParser(gfm_enabled=True)
        return HTMLRenderer(parser=parser, standalone=True)

    def test_render_heading(self, renderer: HTMLRenderer) -> None:
        """Test rendering headings to HTML."""
        block = Block(
            block_type=BlockType.HEADING,
            content="My Heading",
            raw="# My Heading",
            meta={'level': 1}
        )
        html = renderer.render([block])
        assert "<h1>My Heading</h1>" in html

    def test_render_paragraph(self, renderer: HTMLRenderer) -> None:
        """Test rendering paragraphs to HTML."""
        block = Block(
            block_type=BlockType.PARAGRAPH,
            content="This is a paragraph.",
            raw="This is a paragraph."
        )
        html = renderer.render([block])
        assert "<p>This is a paragraph.</p>" in html

    def test_render_code_block(self, renderer: HTMLRenderer) -> None:
        """Test rendering code blocks to HTML."""
        block = Block(
            block_type=BlockType.CODE_BLOCK,
            content="print('hello')",
            raw="```python\nprint('hello')\n```",
            meta={'language': 'python'}
        )
        html = renderer.render([block])
        assert "<pre><code" in html
        assert "language-python" in html

    def test_render_unordered_list(self, renderer: HTMLRenderer) -> None:
        """Test rendering unordered lists to HTML."""
        block = Block(
            block_type=BlockType.UNORDERED_LIST,
            content="Item 1\nItem 2",
            raw="- Item 1\n- Item 2"
        )
        html = renderer.render([block])
        assert "<ul>" in html
        assert "<li>Item 1</li>" in html
        assert "<li>Item 2</li>" in html

    def test_render_ordered_list(self, renderer: HTMLRenderer) -> None:
        """Test rendering ordered lists to HTML."""
        block = Block(
            block_type=BlockType.ORDERED_LIST,
            content="First\nSecond",
            raw="1. First\n2. Second"
        )
        html = renderer.render([block])
        assert "<ol>" in html
        assert "<li>First</li>" in html
        assert "<li>Second</li>" in html

    def test_render_table(self, renderer: HTMLRenderer) -> None:
        """Test rendering tables to HTML."""
        block = Block(
            block_type=BlockType.TABLE,
            content="Header 1|Header 2\nCell 1|Cell 2",
            raw="|Header 1|Header 2|\n|----|----|\n|Cell 1|Cell 2|"
        )
        html = renderer.render([block])
        assert "<table>" in html
        assert "<th>Header 1</th>" in html
        assert "<td>Cell 1</td>" in html

    def test_render_blockquote(self, renderer: HTMLRenderer) -> None:
        """Test rendering blockquotes to HTML."""
        block = Block(
            block_type=BlockType.BLOCKQUOTE,
            content="A quote",
            raw="> A quote"
        )
        html = renderer.render([block])
        assert "<blockquote>A quote</blockquote>" in html

    def test_render_horizontal_rule(self, renderer: HTMLRenderer) -> None:
        """Test rendering horizontal rules to HTML."""
        block = Block(
            block_type=BlockType.HORIZONTAL_RULE,
            content="",
            raw="---"
        )
        html = renderer.render([block])
        assert "<hr>" in html

    def test_render_inline_bold(self, renderer: HTMLRenderer) -> None:
        """Test rendering inline bold text."""
        block = Block(
            block_type=BlockType.PARAGRAPH,
            content="This is **bold** text",
            raw="This is **bold** text"
        )
        html = renderer.render([block])
        assert "<strong>bold</strong>" in html

    def test_render_inline_italic(self, renderer: HTMLRenderer) -> None:
        """Test rendering inline italic text."""
        block = Block(
            block_type=BlockType.PARAGRAPH,
            content="This is *italic* text",
            raw="This is *italic* text"
        )
        html = renderer.render([block])
        assert "<em>italic</em>" in html

    def test_render_inline_code(self, renderer: HTMLRenderer) -> None:
        """Test rendering inline code."""
        block = Block(
            block_type=BlockType.PARAGRAPH,
            content="Use `code` here",
            raw="Use `code` here"
        )
        html = renderer.render([block])
        assert "<code>code</code>" in html

    def test_render_inline_link(self, renderer: HTMLRenderer) -> None:
        """Test rendering inline links."""
        block = Block(
            block_type=BlockType.PARAGRAPH,
            content="Click [here](https://example.com)",
            raw="Click [here](https://example.com)"
        )
        html = renderer.render([block])
        assert '<a href="https://example.com">here</a>' in html

    def test_render_inline_image(self, renderer: HTMLRenderer) -> None:
        """Test rendering inline images."""
        block = Block(
            block_type=BlockType.PARAGRAPH,
            content="![alt text](image.png)",
            raw="![alt text](image.png)"
        )
        html = renderer.render([block])
        assert '<img src="image.png" alt="alt text">' in html

    def test_render_standalone(self, renderer_standalone: HTMLRenderer) -> None:
        """Test rendering standalone HTML document."""
        block = Block(
            block_type=BlockType.PARAGRAPH,
            content="Hello, World!",
            raw="Hello, World!"
        )
        html = renderer_standalone.render_standalone([block], title="Test Page")

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "<title>Test Page</title>" in html
        assert "<style>" in html
        assert "<body>" in html
        assert "<p>Hello, World!</p>" in html

    def test_render_standalone_with_custom_css(self) -> None:
        """Test rendering standalone HTML with custom CSS."""
        parser = MarkdownParser()
        custom_css = "body { background: black; }"
        renderer = HTMLRenderer(parser=parser, standalone=True, css_template=custom_css)

        block = Block(
            block_type=BlockType.HEADING,
            content="Custom",
            raw="# Custom",
            meta={'level': 1}
        )
        html = renderer.render_standalone([block])

        assert custom_css in html

    def test_render_empty_blocks(self, renderer: HTMLRenderer) -> None:
        """Test rendering empty block list."""
        html = renderer.render([])
        assert html == ""

    def test_render_multiple_blocks(self, renderer: HTMLRenderer) -> None:
        """Test rendering multiple blocks."""
        blocks = [
            Block(BlockType.HEADING, "Title", "# Title", meta={'level': 1}),
            Block(BlockType.PARAGRAPH, "Paragraph", "Paragraph"),
            Block(BlockType.CODE_BLOCK, "code", "```\ncode\n```", meta={'language': ''}),
        ]
        html = renderer.render(blocks)

        assert "<h1>Title</h1>" in html
        assert "<p>Paragraph</p>" in html
        assert "<pre><code" in html


class TestIntegration:
    """Integration tests for the complete Markdown to HTML conversion."""

    def test_full_conversion(self) -> None:
        """Test complete Markdown to HTML conversion."""
        from src.parser import MarkdownParser
        from src.renderer import HTMLRenderer

        markdown = """# Document Title

This is a paragraph with **bold** and *italic* text.

## Code Example

```python
def hello():
    print("Hello, World!")
```

## Features

- Feature 1
- Feature 2
- Feature 3

> Important note here

## Data

| Name | Value |
|------|-------|
| Foo  | Bar   |
"""
        parser = MarkdownParser(gfm_enabled=True)
        renderer = HTMLRenderer(parser=parser)

        blocks = parser.parse(markdown)
        html = renderer.render(blocks)

        # Verify key elements
        assert "<h1>Document Title</h1>" in html
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html
        assert "<h2>Code Example</h2>" in html
        assert "language-python" in html
        assert "<h2>Features</h2>" in html
        assert "<li>Feature 1</li>" in html
        assert "<blockquote>" in html
        assert "<h2>Data</h2>" in html
        assert "<table>" in html

    def test_gfm_table_support(self) -> None:
        """Test GFM table support."""
        from src.parser import MarkdownParser

        parser_gfm = MarkdownParser(gfm_enabled=True)
        parser_no_gfm = MarkdownParser(gfm_enabled=False)

        markdown = """| Header |
|-------|
| Cell  |"""

        blocks_gfm = parser_gfm.parse(markdown)
        blocks_no_gfm = parser_no_gfm.parse(markdown)

        assert blocks_gfm[0].block_type == BlockType.TABLE
        assert blocks_no_gfm[0].block_type == BlockType.PARAGRAPH

    def test_escape_html_in_content(self) -> None:
        """Test that HTML in content is escaped."""
        from src.parser import MarkdownParser
        from src.renderer import HTMLRenderer

        parser = MarkdownParser()
        renderer = HTMLRenderer(parser=parser)

        # Markdown with HTML-like content
        markdown = "# Title with <script>alert('xss')</script>"
        blocks = parser.parse(markdown)
        html = renderer.render(blocks)

        # Script tag should be escaped
        assert "&lt;script&gt;" in html
        assert "<script>" not in html
