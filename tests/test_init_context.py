"""Tests for init command context file discovery."""

import os
from pathlib import Path
from unittest.mock import patch


class TestResolvePath:
    """Test resolve_path function."""

    def test_expand_tilde(self):
        """Test that ~ is expanded."""
        from agency.__main__ import resolve_path

        result = resolve_path("~/test.txt")
        assert "~" not in str(result)
        assert result == Path.home() / "test.txt"

    def test_expand_env_var(self):
        """Test that ${VAR} is expanded."""
        from agency.__main__ import resolve_path

        with patch.dict(os.environ, {"TEST_VAR": "myvalue"}):
            result = resolve_path("/path/${TEST_VAR}/file.txt")
            assert result == Path("/path/myvalue/file.txt")

    def test_expand_multiple_env_vars(self):
        """Test that multiple env vars are expanded."""
        from agency.__main__ import resolve_path

        with patch.dict(os.environ, {"VAR1": "a", "VAR2": "b"}):
            result = resolve_path("/${VAR1}/${VAR2}/file.txt")
            assert result == Path("/a/b/file.txt")

    def test_expand_home_env_var(self):
        """Test that ${HOME} is expanded."""
        from agency.__main__ import resolve_path

        result = resolve_path("${HOME}/test.txt")
        assert result == Path.home() / "test.txt"

    def test_expand_tilde_and_env(self):
        """Test that both ~ and env vars work together."""
        from agency.__main__ import resolve_path

        with patch.dict(os.environ, {"PROJECT": "myproject"}):
            result = resolve_path("~/${PROJECT}/file.txt")
            assert "~" not in str(result)
            assert "${PROJECT}" not in str(result)
            assert result == Path.home() / "myproject" / "file.txt"


class TestDiscoverAgentFiles:
    """Test discover_agent_files function."""

    def test_discovers_agents_md_in_home(self, tmp_path):
        """Test that AGENTS.md is discovered in ~/.agents/."""
        from agency.__main__ import discover_agent_files

        # Create ~/.agents/AGENTS.md
        agents_dir = tmp_path / ".agents"
        agents_dir.mkdir()
        agents_md = agents_dir / "AGENTS.md"
        agents_md.write_text("# Agent Config")

        with patch.object(Path, "home", return_value=tmp_path):
            result = discover_agent_files()

        assert result["AGENTS.md"] is not None
        assert result["AGENTS.md"].name == "AGENTS.md"

    def test_discovers_claude_md_in_home(self, tmp_path):
        """Test that CLAUDE.md is discovered in ~/.claude/."""
        from agency.__main__ import discover_agent_files

        # Create ~/.claude/CLAUDE.md
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text("# Claude Config")

        with patch.object(Path, "home", return_value=tmp_path):
            result = discover_agent_files()

        assert result["CLAUDE.md"] is not None
        assert result["CLAUDE.md"].name == "CLAUDE.md"

    def test_discovers_claude_md_in_project_dir(self, tmp_path):
        """Test that CLAUDE.md is discovered in project directory."""
        from agency.__main__ import discover_agent_files

        # Create ~/.claude/projects/myproject/CLAUDE.md
        project_dir = tmp_path / ".claude" / "projects" / "myproject"
        project_dir.mkdir(parents=True)
        claude_md = project_dir / "CLAUDE.md"
        claude_md.write_text("# Claude Project Config")

        with patch.object(Path, "home", return_value=tmp_path):
            result = discover_agent_files("myproject")

        assert result["CLAUDE.md"] is not None
        assert result["CLAUDE.md"].name == "CLAUDE.md"
        assert "myproject" in str(result["CLAUDE.md"])

    def test_returns_none_when_not_found(self, tmp_path):
        """Test that None is returned when no files exist."""
        from agency.__main__ import discover_agent_files

        with patch.object(Path, "home", return_value=tmp_path):
            result = discover_agent_files()

        assert result["AGENTS.md"] is None
        assert result["CLAUDE.md"] is None
        assert result["CLAUDE.local.md"] is None

    def test_priority_order_agents_md(self, tmp_path):
        """Test that AGENTS.md priority is ~/.agents/AGENTS.md > ~/AGENTS.md."""
        from agency.__main__ import discover_agent_files

        # Create both locations
        agents_dir = tmp_path / ".agents"
        agents_dir.mkdir()
        (agents_dir / "AGENTS.md").write_text("# In .agents")
        (tmp_path / "AGENTS.md").write_text("# In home")

        with patch.object(Path, "home", return_value=tmp_path):
            result = discover_agent_files()

        # Should find the one in .agents first
        assert result["AGENTS.md"] == agents_dir / "AGENTS.md"
