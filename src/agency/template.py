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

    def get_cache_path(self, subdir: str = "") -> Path:
        """Get the cache path for a template."""
        # Create a safe cache key from URL
        url_key = self.repo_url.replace("https://github.com/", "").replace("/", "_")
        cache_path = self.cache_dir / url_key

        if subdir:
            cache_path = cache_path / subdir

        return cache_path / ".agency"

    def get_template(self, subdir: str = "", refresh: bool = False) -> Path | None:
        """Get a template, using cache if available."""
        cache_path = self.get_cache_path(subdir)

        if not refresh and cache_path.exists():
            return cache_path

        # Download and extract
        if self._download_template(subdir):
            return cache_path

        return None

    def _download_template(self, subdir: str = "") -> bool:
        """Download template from GitHub."""
        try:
            # Parse the repo URL
            # Format: https://github.com/user/repo or https://github.com/user/repo/tree/branch/path
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

                # Find the extracted directory
                extracted = list(extract_dir.iterdir())[0]

                # Find .agency directory
                if subdir:
                    # Look for subdir/.agency
                    agency_path = extracted / path / subdir / ".agency"
                    if not agency_path.exists():
                        # Try path/.agency where path might include the subdir
                        agency_path = (
                            extracted / (path.split("/")[0] if path else "") / subdir / ".agency"
                        )
                        if not agency_path.exists():
                            agency_path = extracted / subdir / ".agency"
                else:
                    # Look for .agency at various levels
                    agency_path = extracted / path / ".agency" if path else extracted / ".agency"
                    if not agency_path.exists():
                        # Search for any .agency directory
                        for item in extracted.rglob(".agency"):
                            agency_path = item
                            break

                if not agency_path.exists():
                    print("[WARN] Could not find .agency in template archive", flush=True)
                    return False

                # Copy to cache
                cache_path = self.get_cache_path(subdir)
                cache_path.parent.mkdir(parents=True, exist_ok=True)

                if cache_path.exists():
                    shutil.rmtree(cache_path)

                shutil.copytree(agency_path.parent, cache_path.parent / ".agency")

                return True

        except Exception as e:
            print(f"[WARN] Failed to download template: {e}", flush=True)
            return False

    def clear_cache(self, subdir: str = "") -> None:
        """Clear cached template."""
        cache_path = self.get_cache_path(subdir).parent
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
    subdir: str = "basic",
    refresh: bool = False,
) -> Path | None:
    """Download a template and return the path to its .agency directory."""
    tm = TemplateManager(url, cache_dir)
    return tm.get_template(subdir, refresh)
