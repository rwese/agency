"""
Agency v2.0 - Template Management

Handles downloading and extracting project templates from GitHub.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path


class TemplateManager:
    """Manages project templates with caching."""

    def __init__(self, repo_url: str, cache_dir: Path | None = None):
        self.repo_url = repo_url
        self.cache_dir = cache_dir or Path.home() / ".cache" / "agency" / "templates"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_local_templates_dir(self) -> Path | None:
        """Find local templates directory in agency package.

        Checks:
        1. Current working directory/templates/ (development mode)
        2. Agency package directory/templates/ (installed mode)

        Returns:
            Path to local templates directory, or None if not found
        """
        # Try current working directory first (development mode)
        local_dir = Path.cwd() / "templates"
        if local_dir.exists():
            return local_dir

        # Try package directory (installed mode)
        # __file__ is in src/agency/, so parent.parent.parent reaches repo root
        package_dir = Path(__file__).parent.parent.parent
        local_dir = package_dir / "templates"
        if local_dir.exists():
            return local_dir

        return None

    def _parse_url(self) -> tuple[str, str, str]:
        """Parse repo URL into (owner/repo, branch, subdir).

        Returns:
            Tuple of (owner/repo, branch, subdir)
        """
        url = self.repo_url.strip()

        # Handle full URL with /tree/branch/path
        if "/tree/" in url:
            parts = url.split("/tree/")
            repo = parts[0].replace("https://github.com/", "").replace("http://github.com/", "")
            rest = parts[1].split("/")
            branch = rest[0]
            subdir = "/".join(rest[1:]) if len(rest) > 1 else ""
            return repo, branch, subdir

        # Handle just owner/repo (no /tree/)
        if "/" in url:
            if url.startswith("http"):
                repo = url.replace("https://github.com/", "").replace("http://github.com/", "")
                return repo, "main", ""
            else:
                # Just owner/repo format
                return url, "main", ""

        # Simple template name - assume it's in rwese/agency-templates
        return "rwese/agency-templates", "main", url

    def _get_cache_key(self, subdir: str = "") -> str:
        """Get cache key for this template.

        Args:
            subdir: Template subdirectory name
        """
        repo, branch, template_subdir = self._parse_url()

        # Use provided subdir if specified
        if subdir:
            template_subdir = subdir

        repo_key = repo.replace("https://", "").replace("http://", "").replace("/", "_")
        key = f"{repo_key}_{branch}"
        if template_subdir:
            key += f"_{template_subdir.replace('/', '_')}"
        return key

    def get_cache_path(self, subdir: str = "") -> Path:
        """Get the cache directory for this template.

        Args:
            subdir: Template subdirectory name
        """
        return self.cache_dir / self._get_cache_key(subdir)

    def get_template(self, subdir: str = "", refresh: bool = False) -> Path | None:
        """Get a template root path, using cache if available.

        Priority:
        1. Cache (if not refreshing)
        2. Local templates/ directory (agency package)
        3. GitHub download fallback

        Args:
            subdir: Optional subdirectory within the template (e.g., 'fullstack-ts')
            refresh: Force re-download even if cached

        Returns:
            Path to template root directory, or None if download failed
        """
        # Use 'basic' as default if no subdir specified
        effective_subdir = subdir if subdir else "basic"
        cache_path = self.get_cache_path(effective_subdir)

        # Check cache first
        if not refresh and cache_path.exists() and any(cache_path.iterdir()):
            return cache_path

        # Try local templates first
        if self._copy_local_template(effective_subdir, cache_path):
            return cache_path

        # Fall back to GitHub download
        if self._download_template(effective_subdir):
            return cache_path

        return None

    def _copy_local_template(self, subdir: str, cache_path: Path) -> bool:
        """Copy template from local templates/ directory.

        Args:
            subdir: Template subdirectory name (e.g., 'basic')
            cache_path: Where to copy the template

        Returns:
            True if copied successfully, False otherwise
        """
        if not subdir:
            subdir = "basic"

        local_templates = self._get_local_templates_dir()
        if not local_templates:
            return False

        template_source = local_templates / subdir
        if not template_source.exists():
            return False

        try:
            if cache_path.exists():
                shutil.rmtree(cache_path)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(template_source, cache_path)
            return True
        except Exception as e:
            print(f"[WARN] Local template copy failed: {e}", flush=True)
            return False

    def _download_template(self, subdir: str = "") -> bool:
        """Download template from GitHub.

        Args:
            subdir: Subdirectory within the template to use

        Returns:
            True if successful, False otherwise
        """
        try:
            repo, branch, template_subdir = self._parse_url()

            # Use provided subdir if specified
            if subdir:
                template_subdir = subdir
            if not template_subdir:
                template_subdir = "basic"

            # Build archive URL
            archive_url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"

            with tempfile.TemporaryDirectory() as tmpdir:
                tmppath = Path(tmpdir)
                zip_path = tmppath / "template.zip"
                extract_dir = tmppath / "extracted"

                # Download
                result = subprocess.run(
                    ["curl", "-sL", "-o", str(zip_path), archive_url], capture_output=True, text=True, timeout=60
                )

                if result.returncode != 0:
                    print(f"[WARN] curl failed: {result.stderr}", flush=True)
                    return False

                if not zip_path.exists() or zip_path.stat().st_size < 100:
                    print("[WARN] Downloaded file is invalid or empty", flush=True)
                    return False

                # Extract
                result = subprocess.run(
                    ["unzip", "-q", str(zip_path), "-d", str(extract_dir)], capture_output=True, text=True, timeout=60
                )

                if result.returncode != 0:
                    print(f"[WARN] unzip failed: {result.stderr}", flush=True)
                    return False

                # Find extracted directory (repo-branch-xxx)
                extracted_items = list(extract_dir.iterdir())
                if not extracted_items:
                    print("[WARN] Nothing extracted", flush=True)
                    return False

                repo_dir = extracted_items[0]

                # Navigate to the template subdirectory if specified
                template_root = repo_dir
                if template_subdir and template_subdir != ".":
                    for part in template_subdir.split("/"):
                        if part:
                            next_path = template_root / part
                            if next_path.exists():
                                template_root = next_path
                            else:
                                print(f"[WARN] Subdirectory '{part}' not found in template", flush=True)
                                break

                if not template_root.exists():
                    print("[WARN] Template root not found", flush=True)
                    return False

                # Copy to cache
                cache_path = self.get_cache_path()
                if cache_path.exists():
                    shutil.rmtree(cache_path)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(template_root, cache_path)

                return True

        except subprocess.TimeoutExpired:
            print("[WARN] Template download timed out", flush=True)
            return False
        except Exception as e:
            print(f"[WARN] Template download failed: {e}", flush=True)
            return False

    def clear_cache(self) -> None:
        """Clear cached template."""
        cache_path = self.get_cache_path()
        if cache_path.exists():
            shutil.rmtree(cache_path)

    def clear_all_cache(self) -> None:
        """Clear all cached templates."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


def download_template(
    url: str,
    cache_dir: Path | None = None,
    subdir: str = "",
    refresh: bool = False,
) -> Path | None:
    """Download a template and return the path to its root directory.

    Args:
        url: Template URL or name (e.g., 'fullstack-ts' or full GitHub URL)
        cache_dir: Optional cache directory
        subdir: Subdirectory within template
        refresh: Force re-download

    Returns:
        Path to template root, or None if failed
    """
    tm = TemplateManager(url, cache_dir)
    return tm.get_template(subdir, refresh)
