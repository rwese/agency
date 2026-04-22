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

    def _url_to_cache_key(self) -> str:
        """Convert repo URL to a safe cache key."""
        # Extract repo from URL first
        url = self.repo_url
        if "/tree/" in url:
            # https://github.com/user/repo/tree/branch/path -> user_repo
            repo = url.split("/tree/")[0].replace("https://github.com/", "")
        else:
            repo = url.replace("https://github.com/", "")
        return repo.replace("/", "_")

    def get_cache_root(self, subdir: str = "") -> Path:
        """Get the cache root path for a template (the template directory itself)."""
        url_key = self._url_to_cache_key()
        cache_path = self.cache_dir / url_key
        if subdir:
            cache_path = cache_path / subdir
        return cache_path

    def get_template(self, subdir: str = "", refresh: bool = False) -> Path | None:
        """Get a template root path, using cache if available."""
        cache_root = self.get_cache_root(subdir)

        if not refresh and cache_root.exists():
            return cache_root

        # Download and extract
        if self._download_template(subdir):
            return cache_root

        return None

    def _download_template(self, subdir: str = "") -> bool:
        """Download template from GitHub."""
        try:
            # Parse the repo URL
            url = self.repo_url

            # Handle full URLs with tree
            if "/tree/" in url:
                parts = url.split("/tree/")
                repo = parts[0].replace("https://github.com/", "")
                rest = parts[1].split("/", 1)
                branch = rest[0]
                path = rest[1] if len(rest) > 1 else ""
            else:
                repo = url.replace("https://github.com/", "")
                branch = "main"
                path = ""

            # Build archive URL
            archive_url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"

            # Download to temp directory
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / "template.zip"

                # Download
                result = subprocess.run(
                    ["curl", "-sL", "-o", str(zip_path), archive_url],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(f"[WARN] Failed to download template: {result.stderr}", flush=True)
                    return False

                # Extract
                extract_dir = Path(tmpdir) / "extracted"
                extract_dir.mkdir()

                result = subprocess.run(
                    ["unzip", "-q", str(zip_path), "-d", str(extract_dir)],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(f"[WARN] Failed to extract template: {result.stderr}", flush=True)
                    return False

                # Find the extracted directory (repo-branch-xxx)
                extracted = list(extract_dir.iterdir())[0]

                # Find .agency directory
                if subdir:
                    # Look for subdir/.agency
                    agency_path = extracted / path / subdir / ".agency" if path else extracted / subdir / ".agency"
                    if not agency_path.exists():
                        agency_path = extracted / subdir / ".agency"
                else:
                    agency_path = extracted / path / ".agency" if path else extracted / ".agency"
                    if not agency_path.exists():
                        for item in extracted.rglob(".agency"):
                            agency_path = item
                            break

                if not agency_path.exists():
                    print("[WARN] Could not find .agency in template archive", flush=True)
                    return False

                # Determine template root (directory containing .agency)
                template_root = agency_path.parent
                
                # Copy entire template directory to cache
                cache_root = self.get_cache_root(subdir)
                cache_root.parent.mkdir(parents=True, exist_ok=True)

                if cache_root.exists():
                    shutil.rmtree(cache_root)

                # Copy the entire template root (includes .agency and all project files)
                shutil.copytree(template_root, cache_root)

                return True

        except Exception as e:
            print(f"[WARN] Failed to download template: {e}", flush=True)
            return False

    def clear_cache(self, subdir: str = "") -> None:
        """Clear cached template."""
        cache_root = self.get_cache_root(subdir)
        if cache_root.exists():
            shutil.rmtree(cache_root.parent)

    def clear_all_cache(self) -> None:
        """Clear all cached templates."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


def download_template(
    url: str,
    cache_dir: Path | None = None,
    subdir: str = "basic",
    refresh: bool = False,
) -> Path | None:
    """Download a template and return the path to its root directory."""
    tm = TemplateManager(url, cache_dir)
    return tm.get_template(subdir, refresh)
