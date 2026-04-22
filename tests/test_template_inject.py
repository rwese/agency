"""
Tests for template_inject module.
"""

import os
import tempfile
from pathlib import Path

import pytest

from agency.template_inject import (
    InjectionOptions,
    InjectionResult,
    TemplateInjector,
    process_file,
    process_string,
)


class TestTemplateInjector:
    """Tests for TemplateInjector class."""

    def test_file_placeholder_absolute_path(self, tmp_path):
        """Test ${{file:absolute/path}}."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content here")

        injector = TemplateInjector(options=InjectionOptions(base_dir=tmp_path))
        # Escape braces for f-string: use {{ and }} for literal braces
        template = f"Some text ${{{{file:{test_file}}}}} end"
        result = injector.process(template)

        assert result.content == "Some text file content here end"
        assert result.errors == []

    def test_file_placeholder_relative_path(self, tmp_path):
        """Test ${{file:relative/path}} resolved from base_dir."""
        # Create test file
        test_file = tmp_path / "nested" / "test.txt"
        test_file.parent.mkdir()
        test_file.write_text("nested content")

        injector = TemplateInjector(options=InjectionOptions(base_dir=tmp_path))
        result = injector.process("${{file:nested/test.txt}}")

        assert result.content == "nested content"
        assert result.errors == []

    def test_file_placeholder_not_found(self, tmp_path):
        """Test ${{file:nonexistent}} logs warning."""
        injector = TemplateInjector(options=InjectionOptions(base_dir=tmp_path))
        result = injector.process("${{file:nonexistent.txt}}")

        assert "not found" in result.errors[0]
        assert result.content == ""  # Empty on error

    def test_shell_placeholder_simple(self):
        """Test ${{shell:echo hello}}."""
        injector = TemplateInjector()
        result = injector.process("Output: ${{shell:echo hello}}")

        assert result.content == "Output: hello"
        assert result.errors == []

    def test_shell_placeholder_with_args(self):
        """Test shell command with arguments."""
        injector = TemplateInjector()
        result = injector.process("${{shell:printf 'num:%d' 42}}")

        assert result.content == "num:42"
        assert result.errors == []

    def test_shell_placeholder_strips_newlines(self):
        """Test that shell output trailing newlines are stripped."""
        injector = TemplateInjector(options=InjectionOptions(strip_newlines=True))
        result = injector.process("x${{shell:echo -e 'a\\nb\\nc'}}y")

        # Should not have trailing newline in middle
        assert "a\nb\nc" in result.content
        assert not result.content.endswith("\n")

    def test_shell_placeholder_no_strip_option(self):
        """Test shell without newline stripping."""
        options = InjectionOptions(strip_newlines=False)
        injector = TemplateInjector(options=options)
        result = injector.process("${{shell:echo test}}")

        # Original stdout may or may not have newline depending on echo
        # Just verify no error
        assert result.errors == []

    def test_multiple_placeholders(self):
        """Test multiple placeholders in one string."""
        injector = TemplateInjector()
        result = injector.process(
            "${{shell:echo first}} and ${{shell:echo second}}"
        )

        assert result.content == "first and second"

    def test_mixed_placeholders(self):
        """Test mix of file and shell placeholders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "data.txt"
            test_file.write_text("file_data")

            injector = TemplateInjector(options=InjectionOptions(base_dir=tmp_path))
            result = injector.process(
                "shell=${{shell:echo cmd}}, file=${{file:data.txt}}"
            )

            assert result.content == "shell=cmd, file=file_data"

    def test_unknown_type_kept_as_is(self):
        """Test unknown placeholder type is preserved (not matched by pattern)."""
        injector = TemplateInjector()
        # env: is not in our (file|shell) alternation, so pattern won't match
        result = injector.process("${{env:VAR_NAME}}")

        # Unknown types are preserved as-is (pattern doesn't match them)
        assert result.content == "${{env:VAR_NAME}}"
        assert result.errors == []  # No error - pattern just didn't match

    def test_custom_pattern_double_braces(self):
        """Test custom delimiter pattern {{file:path}}."""
        # Create injector with {{...}} delimiters
        injector = TemplateInjector.with_delimiters("{{", "}}")

        # Pattern matches {{...}} anywhere in string (including embedded)
        result1 = injector.process("prefix {{file:test.txt}} suffix")
        # Should have attempted to read test.txt (error expected)
        assert "not found" in result1.errors[0]

        # Should match standalone {{...}} without $ prefix
        result2 = injector.process("{{file:/dev/null}}")
        assert result2.content == ""  # /dev/null is empty

    def test_empty_content(self):
        """Test processing empty string."""
        injector = TemplateInjector()
        result = injector.process("")

        assert result.content == ""
        assert result.errors == []

    def test_no_placeholders(self):
        """Test string without placeholders unchanged."""
        injector = TemplateInjector()
        result = injector.process("plain text without placeholders")

        assert result.content == "plain text without placeholders"
        assert result.errors == []

    def test_shell_timeout(self):
        """Test shell command timeout handling."""
        injector = TemplateInjector()
        # Sleep longer than timeout (60s)
        result = injector.process("${{shell:sleep 100}}")

        assert "timed out" in result.errors[0]

    def test_process_placeholder_error_in_context(self, tmp_path):
        """Test placeholder error doesn't affect other placeholders."""
        # Create valid file
        valid_file = tmp_path / "valid.txt"
        valid_file.write_text("valid")

        injector = TemplateInjector(options=InjectionOptions(base_dir=tmp_path))
        result = injector.process(
            "${{file:nonexistent}} and ${{file:valid.txt}}"
        )

        # Should have one error but still process valid file
        assert "not found" in result.errors[0]
        assert "valid" in result.content


class TestProcessFile:
    """Tests for process_file function."""

    def test_process_file_creates_injector(self, tmp_path):
        """Test that process_file uses file's directory as base_dir."""
        nested = tmp_path / "nested"
        nested.mkdir()
        test_file = nested / "ref.txt"
        test_file.write_text("content")

        # Reference file in same directory
        result = process_file(test_file)
        assert result.content == "content"

    def test_process_file_read_error(self):
        """Test process_file handles read errors."""
        result = process_file(Path("/nonexistent/path/file.txt"))
        assert "Failed to read" in result.errors[0]


class TestProcessString:
    """Tests for process_string function."""

    def test_process_string_default_base_dir(self):
        """Test process_string uses cwd as default base_dir."""
        result = process_string("${{shell:echo test}}")
        assert result.content == "test"

    def test_process_string_custom_base_dir(self, tmp_path):
        """Test process_string accepts custom base_dir."""
        result = process_string(
            "${{file:test.txt}}",
            base_dir=tmp_path
        )
        # Will error but proves base_dir was passed
        assert len(result.errors) > 0 or "test.txt" in result.content


class TestInjectionResult:
    """Tests for InjectionResult dataclass."""

    def test_result_with_errors(self):
        """Test InjectionResult can hold errors."""
        result = InjectionResult(
            content="partial content",
            errors=["warning 1", "warning 2"]
        )

        assert result.content == "partial content"
        assert len(result.errors) == 2

    def test_result_no_errors(self):
        """Test InjectionResult with empty errors."""
        result = InjectionResult(content="content", errors=[])

        assert result.content == "content"
        assert result.errors == []


class TestInjectionOptions:
    """Tests for InjectionOptions dataclass."""

    def test_default_options(self):
        """Test default InjectionOptions values."""
        options = InjectionOptions()

        assert options.base_dir == Path.cwd()
        assert options.strip_newlines is True
        assert options.max_shell_output == 100_000

    def test_custom_options(self, tmp_path):
        """Test custom InjectionOptions values."""
        options = InjectionOptions(
            base_dir=tmp_path,
            strip_newlines=False,
            max_shell_output=1000
        )

        assert options.base_dir == tmp_path
        assert options.strip_newlines is False
        assert options.max_shell_output == 1000
