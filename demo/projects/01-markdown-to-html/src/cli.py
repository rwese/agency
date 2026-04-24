"""Command-line interface for the Markdown to HTML converter.

This module provides the CLI entry point for the md2html tool.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import TextIO

from src.parser import MarkdownParser
from src.renderer import HTMLRenderer


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog='md2html',
        description='Convert Markdown files to HTML with syntax highlighting.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  md2html input.md -o output.html
  md2html input.md --standalone -o output.html
  md2html input.md --watch -o output.html
  md2html input.md --template custom.css -o output.html
        """
    )

    parser.add_argument(
        'input',
        type=pathlib.Path,
        nargs='?',
        help='Input Markdown file (reads from stdin if not provided)'
    )

    parser.add_argument(
        '-o', '--output',
        type=pathlib.Path,
        help='Output HTML file (writes to stdout if not provided)'
    )

    parser.add_argument(
        '-s', '--standalone',
        action='store_true',
        help='Generate standalone HTML with embedded CSS'
    )

    parser.add_argument(
        '-t', '--template',
        type=pathlib.Path,
        dest='css_template',
        help='Custom CSS file to use for standalone output'
    )

    parser.add_argument(
        '-w', '--watch',
        action='store_true',
        help='Watch input file for changes and rebuild'
    )

    parser.add_argument(
        '--title',
        type=str,
        default='Document',
        help='Page title for standalone output (default: "Document")'
    )

    parser.add_argument(
        '--no-gfm',
        action='store_true',
        help='Disable GitHub Flavored Markdown extensions'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress non-error output'
    )

    return parser


def read_input(source: pathlib.Path | TextIO | None) -> str:
    """Read Markdown input from a file or stdin.

    Args:
        source: File path or stdin stream.

    Returns:
        The input content as a string.

    Raises:
        FileNotFoundError: If the input file doesn't exist.
        IsADirectoryError: If the input is a directory.
    """
    if source is None:
        return sys.stdin.read()

    if isinstance(source, pathlib.Path):
        if source.is_dir():
            raise IsADirectoryError(f"'{source}' is a directory")
        return source.read_text(encoding='utf-8')

    return source.read()


def write_output(content: str, destination: pathlib.Path | None, quiet: bool = False) -> None:
    """Write HTML output to a file or stdout.

    Args:
        content: The HTML content to write.
        destination: File path or None for stdout.
        quiet: Whether to suppress success message.
    """
    if destination:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding='utf-8')
        if not quiet:
            print(f"✓ Written to {destination}")
    else:
        print(content)


def convert(
    input_source: pathlib.Path | TextIO | None,
    output_destination: pathlib.Path | None = None,
    standalone: bool = False,
    css_template: pathlib.Path | None = None,
    title: str = "Document",
    gfm_enabled: bool = True,
    quiet: bool = False
) -> str:
    """Convert Markdown to HTML.

    Args:
        input_source: Input file path or stdin.
        output_destination: Output file path.
        standalone: Whether to generate standalone HTML.
        css_template: Custom CSS file for standalone output.
        title: Page title for standalone output.
        gfm_enabled: Whether to enable GFM extensions.
        quiet: Whether to suppress output messages.

    Returns:
        The generated HTML content.
    """
    # Read input
    markdown = read_input(input_source)

    # Parse Markdown
    parser = MarkdownParser(gfm_enabled=gfm_enabled)
    blocks = parser.parse(markdown)

    # Load custom CSS if provided
    custom_css = None
    if css_template and css_template.exists():
        custom_css = css_template.read_text(encoding='utf-8')

    # Render HTML
    renderer = HTMLRenderer(
        parser=parser,
        standalone=standalone,
        css_template=custom_css
    )

    if standalone:
        html = renderer.render_standalone(blocks, title=title)
    else:
        html = renderer.render(blocks)

    # Write output
    write_output(html, output_destination, quiet=quiet)

    return html


def watch_file(
    input_path: pathlib.Path,
    output_path: pathlib.Path,
    standalone: bool = False,
    css_template: pathlib.Path | None = None,
    title: str = "Document",
    gfm_enabled: bool = True
) -> None:
    """Watch input file and rebuild on changes.

    Args:
        input_path: Input file to watch.
        output_path: Output file to write.
        standalone: Whether to generate standalone HTML.
        css_template: Custom CSS file for standalone output.
        title: Page title for standalone output.
        gfm_enabled: Whether to enable GFM extensions.
    """
    import time

    print(f"👀 Watching {input_path} for changes...")

    # Get initial modification time
    last_mtime = input_path.stat().st_mtime

    while True:
        try:
            current_mtime = input_path.stat().st_mtime
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                print("\n📝 Change detected, rebuilding...")
                try:
                    convert(
                        input_source=input_path,
                        output_destination=output_path,
                        standalone=standalone,
                        css_template=css_template,
                        title=title,
                        gfm_enabled=gfm_enabled,
                        quiet=False
                    )
                except Exception as e:
                    print(f"✗ Error: {e}")
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\n👋 Stopped watching.")
            break


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments (uses sys.argv if None).

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        # Handle watch mode
        if args.watch:
            if not args.input:
                parser.error("--watch requires an input file")
            if not args.output:
                parser.error("--watch requires an output file")

            watch_file(
                input_path=args.input,
                output_path=args.output,
                standalone=args.standalone,
                css_template=args.css_template,
                title=args.title,
                gfm_enabled=not args.no_gfm
            )
            return 0

        # Normal conversion
        convert(
            input_source=args.input,
            output_destination=args.output,
            standalone=args.standalone,
            css_template=args.css_template,
            title=args.title,
            gfm_enabled=not args.no_gfm,
            quiet=args.quiet
        )
        return 0

    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1
    except IsADirectoryError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        if not args.quiet:
            raise
        return 1


if __name__ == '__main__':
    sys.exit(main())
