"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest
import yaml

from agency.config import (
    AgencyConfig,
    AgentConfig,
    ManagerConfig,
    load_agency_config,
    load_agents_config,
    load_manager_config,
    save_agency_config,
    save_agents_config,
    save_manager_config,
)


class TestAgencyConfig:
    """Test AgencyConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AgencyConfig(project="test-project")

        assert config.project == "test-project"
        assert config.shell == "bash"
        assert config.template_url == "https://github.com/rwese/agency-templates"
        assert config.stop_timeout == 30

    def test_custom_values(self):
        """Test custom configuration values."""
        config = AgencyConfig(
            project="api",
            shell="zsh",
            template_url="https://github.com/user/repo",
            stop_timeout=60,
        )

        assert config.project == "api"
        assert config.shell == "zsh"
        assert config.template_url == "https://github.com/user/repo"
        assert config.stop_timeout == 60


class TestManagerConfig:
    """Test ManagerConfig dataclass."""

    def test_default_values(self):
        """Test default manager configuration."""
        config = ManagerConfig(
            name="coordinator",
            personality="You are a coordinator.",
        )

        assert config.name == "coordinator"
        assert config.personality == "You are a coordinator."
        assert config.poll_interval == 30
        assert config.auto_approve is False
        assert config.max_retries is None


class TestAgentConfig:
    """Test AgentConfig dataclass."""

    def test_required_fields(self):
        """Test required fields."""
        config = AgentConfig(name="coder")

        assert config.name == "coder"
        assert config.personality is None


class TestLoadAgencyConfig:
    """Test loading agency configuration."""

    @pytest.fixture
    def temp_agency_dir(self):
        """Create a temporary .agency directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agency_dir = Path(tmpdir) / ".agency"
            agency_dir.mkdir()
            yield agency_dir

    def test_load_nonexistent(self, temp_agency_dir):
        """Test loading config when file doesn't exist."""
        config = load_agency_config(temp_agency_dir)

        assert config.project == temp_agency_dir.parent.name
        assert config.shell == "bash"

    def test_load_existing(self, temp_agency_dir):
        """Test loading existing configuration."""
        config_file = temp_agency_dir / "config.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "project": "myapi",
                    "shell": "zsh",
                    "template_url": "https://example.com",
                    "stop_timeout": 45,
                }
            )
        )

        config = load_agency_config(temp_agency_dir)

        assert config.project == "myapi"
        assert config.shell == "zsh"
        assert config.template_url == "https://example.com"
        assert config.stop_timeout == 45


class TestLoadManagerConfig:
    """Test loading manager configuration."""

    @pytest.fixture
    def temp_agency_dir(self):
        """Create a temporary .agency directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agency_dir = Path(tmpdir) / ".agency"
            agency_dir.mkdir()
            yield agency_dir

    def test_load_nonexistent(self, temp_agency_dir):
        """Test loading manager config when file doesn't exist."""
        config = load_manager_config(temp_agency_dir)

        assert config is None

    def test_load_existing(self, temp_agency_dir):
        """Test loading existing manager configuration."""
        config_file = temp_agency_dir / "manager.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "name": "coordinator",
                    "personality": "You are a manager.",
                    "poll_interval": 60,
                    "auto_approve": True,
                    "max_retries": 3,
                }
            )
        )

        config = load_manager_config(temp_agency_dir)

        assert config is not None
        assert config.name == "coordinator"
        assert config.personality == "You are a manager."
        assert config.poll_interval == 60
        assert config.auto_approve is True
        assert config.max_retries == 3


class TestLoadAgentsConfig:
    """Test loading agents configuration."""

    @pytest.fixture
    def temp_agency_dir(self):
        """Create a temporary .agency directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agency_dir = Path(tmpdir) / ".agency"
            agency_dir.mkdir()
            yield agency_dir

    def test_load_nonexistent(self, temp_agency_dir):
        """Test loading agents config when file doesn't exist."""
        agents = load_agents_config(temp_agency_dir)

        assert agents == []

    def test_load_with_configs(self, temp_agency_dir):
        """Test loading agents with individual configs."""
        # Create agents directory
        agents_dir = temp_agency_dir / "agents"
        agents_dir.mkdir()

        # Create agents.yaml
        agents_file = temp_agency_dir / "agents.yaml"
        agents_file.write_text(
            yaml.dump(
                {
                    "agents": [
                        {"name": "coder", "config": "agents/coder.yaml"},
                        {"name": "tester", "config": "agents/tester.yaml"},
                    ]
                }
            )
        )

        # Create coder config
        coder_file = agents_dir / "coder.yaml"
        coder_file.write_text(
            yaml.dump(
                {
                    "name": "coder",
                    "personality": "Senior developer",
                }
            )
        )

        # Create tester config
        tester_file = agents_dir / "tester.yaml"
        tester_file.write_text(
            yaml.dump(
                {
                    "name": "tester",
                    "personality": "QA engineer",
                }
            )
        )

        agents = load_agents_config(temp_agency_dir)

        assert len(agents) == 2
        assert agents[0].name == "coder"
        assert agents[0].personality == "Senior developer"
        assert agents[1].name == "tester"
        assert agents[1].personality == "QA engineer"


class TestSaveAgencyConfig:
    """Test saving agency configuration."""

    @pytest.fixture
    def temp_agency_dir(self):
        """Create a temporary .agency directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agency_dir = Path(tmpdir) / ".agency"
            agency_dir.mkdir()
            yield agency_dir

    def test_save_config(self, temp_agency_dir):
        """Test saving agency configuration."""
        config = AgencyConfig(
            project="new-project",
            shell="zsh",
            template_url="https://example.com",
            stop_timeout=90,
        )

        save_agency_config(temp_agency_dir, config)

        config_file = temp_agency_dir / "config.yaml"
        assert config_file.exists()

        loaded = yaml.safe_load(config_file.read_text())
        assert loaded["project"] == "new-project"
        assert loaded["shell"] == "zsh"
        assert loaded["template_url"] == "https://example.com"
        assert loaded["stop_timeout"] == 90


class TestSaveManagerConfig:
    """Test saving manager configuration."""

    @pytest.fixture
    def temp_agency_dir(self):
        """Create a temporary .agency directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agency_dir = Path(tmpdir) / ".agency"
            agency_dir.mkdir()
            yield agency_dir

    def test_save_config(self, temp_agency_dir):
        """Test saving manager configuration."""
        config = ManagerConfig(
            name="coordinator",
            personality="You are a coordinator.",
            poll_interval=45,
            auto_approve=True,
            max_retries=5,
        )

        save_manager_config(temp_agency_dir, config)

        config_file = temp_agency_dir / "manager.yaml"
        assert config_file.exists()

        loaded = yaml.safe_load(config_file.read_text())
        assert loaded["name"] == "coordinator"
        assert loaded["personality"] == "You are a coordinator."
        assert loaded["poll_interval"] == 45
        assert loaded["auto_approve"] is True
        assert loaded["max_retries"] == 5


class TestSaveAgentsConfig:
    """Test saving agents configuration."""

    @pytest.fixture
    def temp_agency_dir(self):
        """Create a temporary .agency directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agency_dir = Path(tmpdir) / ".agency"
            agency_dir.mkdir()
            yield agency_dir

    def test_save_config(self, temp_agency_dir):
        """Test saving agents configuration."""
        agents = [
            AgentConfig(name="coder", personality="Senior developer"),
            AgentConfig(name="tester", personality="QA engineer"),
        ]

        save_agents_config(temp_agency_dir, agents)

        # Check agents.yaml
        agents_file = temp_agency_dir / "agents.yaml"
        assert agents_file.exists()

        loaded = yaml.safe_load(agents_file.read_text())
        assert len(loaded["agents"]) == 2

        # Check individual configs
        coder_file = temp_agency_dir / "agents" / "coder.yaml"
        assert coder_file.exists()

        coder_loaded = yaml.safe_load(coder_file.read_text())
        assert coder_loaded["name"] == "coder"
        assert coder_loaded["personality"] == "Senior developer"
