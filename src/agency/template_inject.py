"""
Agency v2.0 - Template Injection

Provides dynamic placeholder injection into personality and context files.

Supported placeholders:
- ${{file:path}}      → Read file at path, inject contents
- ${{shell:cmd}}       → Execute command, inject stdout

Syntax: ${{type:value}}
- type: file or shell
- value: path or command
"""

import re
import subprocess
from pathlib import Path

from pydantic import BaseModel, Field


class InjectionResult(BaseModel):
    """Result of processing a template."""

    content: str
    errors: list[str] = Field(default_factory=list)  # Non-fatal errors encountered


class InjectionOptions(BaseModel):
    """Options for template injection."""

    base_dir: Path = Field(default_factory=Path.cwd)  # Base directory for relative file paths
    strip_newlines: bool = True  # Strip trailing newlines from shell output
    max_shell_output: int = 100_000  # Max bytes from shell command


class TemplateInjector:
    """Processes templates with dynamic placeholder injection."""

    # Default pattern: ${{type:value}}
    DEFAULT_PATTERN = r"\$\{\{((?:file|shell):[^\}]+)\}\}"

    def __init__(
        self,
        pattern: str | None = None,
        options: InjectionOptions | None = None,
    ):
        r"""Initialize injector.

        Args:
            pattern: Custom regex pattern for placeholders. Must have one capture group
                     containing the full placeholder (type:value). Example: r"\{\{(file|shell):([^}]+)\}\}"
            options: Injection options
        """
        self.options = options or InjectionOptions()
        self._pattern = re.compile(pattern or self.DEFAULT_PATTERN)

    @classmethod
    def with_delimiters(
        cls,
        open_delim: str,
        close_delim: str,
        options: InjectionOptions | None = None,
    ) -> "TemplateInjector":
        r"""Create injector with custom delimiters.

        Example: cls.with_delimiters("{{", "}}") creates pattern: r"\{\{(file|shell):[^\}]+\}\}"

        Args:
            open_delim: Opening delimiter (will be escaped)
            close_delim: Closing delimiter (will be escaped)
        """
        # Escape the delimiters for regex
        open_esc = re.escape(open_delim)
        close_esc = re.escape(close_delim)

        # Build pattern: open_delim(type:value)close_delim
        # Character class: [^{close_esc}] means any char except close_delim chars
        pattern = f"{open_esc}((?:file|shell):[^{close_esc}]+){close_esc}"
        return cls(pattern=pattern, options=options)

    def _parse_placeholder(self, placeholder: str) -> tuple[str, str]:
        """Parse placeholder into (type, value).

        Args:
            placeholder: Full placeholder string (e.g., "file:./config.md")

        Returns:
            Tuple of (type, value)
        """
        if ":" not in placeholder:
            return "", placeholder

        type_part, _, value_part = placeholder.partition(":")
        return type_part.strip(), value_part.strip()

    def _process_file(self, path_str: str) -> tuple[str, str | None]:
        """Read file and return contents.

        Args:
            path_str: File path (relative or absolute)

        Returns:
            Tuple of (content, error_message or None)
        """
        # Resolve relative paths from base_dir
        path = Path(path_str)
        if not path.is_absolute():
            path = self.options.base_dir / path

        try:
            content = path.read_text(encoding="utf-8")
            return content, None
        except FileNotFoundError:
            return "", f"[WARN] Template file not found: {path}"
        except PermissionError:
            return "", f"[WARN] Template file permission denied: {path}"
        except UnicodeDecodeError:
            return "", f"[WARN] Template file not valid UTF-8: {path}"
        except Exception as e:
            return "", f"[WARN] Template file read error: {path}: {e}"

    def _process_shell(self, command: str) -> tuple[str, str | None]:
        """Execute shell command and return stdout.

        Args:
            command: Shell command to execute

        Returns:
            Tuple of (stdout_content, error_message or None)
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
            )

            # Return stdout (strip newlines if configured)
            output = result.stdout
            if self.options.strip_newlines:
                output = output.rstrip("\n\r")

            # Check for non-zero exit (still return output, but log warning)
            if result.returncode != 0:
                stderr_preview = result.stderr[:200] if result.stderr else "no stderr"
                return output, f"[WARN] Shell command exited {result.returncode}: {stderr_preview}"

            # Warn if output was truncated
            if len(result.stdout.encode("utf-8")) > self.options.max_shell_output:
                return output[
                    : self.options.max_shell_output
                ], f"[WARN] Shell output truncated to {self.options.max_shell_output} bytes"

            return output, None

        except subprocess.TimeoutExpired:
            return "", "[WARN] Shell command timed out after 60s"
        except Exception as e:
            return "", f"[WARN] Shell command failed: {e}"

    def _process_placeholder(self, match: re.Match) -> str:
        """Process a single placeholder match.

        Args:
            match: Regex match object

        Returns:
            Replacement string or original placeholder on error
        """
        full_placeholder = match.group(1)
        placeholder_type, value = self._parse_placeholder(full_placeholder)

        if placeholder_type == "file":
            content, error = self._process_file(value)
            if error:
                self._last_errors.append(error)
            return content

        elif placeholder_type == "shell":
            content, error = self._process_shell(value)
            if error:
                self._last_errors.append(error)
            return content

        else:
            self._last_errors.append(f"[WARN] Unknown placeholder type '{placeholder_type}'")
            return match.group(0)  # Return original

    def process(self, content: str) -> InjectionResult:
        """Process a template string, replacing all placeholders.

        Args:
            content: Template string with placeholders

        Returns:
            InjectionResult with processed content and any errors
        """
        self._last_errors: list[str] = []

        # Replace all placeholders
        result = self._pattern.sub(self._process_placeholder, content)

        return InjectionResult(content=result, errors=self._last_errors.copy())


def process_file(
    file_path: Path,
    options: InjectionOptions | None = None,
    pattern: str | None = None,
) -> InjectionResult:
    """Process a file, replacing all placeholders in its content.

    Args:
        file_path: Path to file to process
        options: Injection options (uses file's directory as base_dir if not provided)
        pattern: Custom regex pattern

    Returns:
        InjectionResult with processed content
    """
    if options is None:
        options = InjectionOptions(base_dir=file_path.parent)

    injector = TemplateInjector(pattern=pattern, options=options)

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return InjectionResult(content="", errors=[f"Failed to read file: {e}"])

    return injector.process(content)


def process_string(
    content: str,
    base_dir: Path | None = None,
    pattern: str | None = None,
) -> InjectionResult:
    """Process a template string.

    Args:
        content: Template string with placeholders
        base_dir: Base directory for relative file paths
        pattern: Custom regex pattern

    Returns:
        InjectionResult with processed content
    """
    options = InjectionOptions(base_dir=base_dir or Path.cwd())
    injector = TemplateInjector(pattern=pattern, options=options)
    return injector.process(content)
