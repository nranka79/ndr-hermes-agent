#!/usr/bin/env python3
"""
GitHub sync daemon for Hermes - backs up learned skills to GitHub.
Uses GitHub REST API (no git CLI required).
Runs as background process in Railway container.
"""

import os
import time
import json
import hashlib
import requests
from datetime import datetime
from pathlib import Path

HERMES_HOME = os.environ.get("HERMES_HOME", "/data/hermes")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
GITHUB_USER = os.environ.get("GITHUB_USER", "nranka79")
SYNC_INTERVAL = 300  # 5 minutes

# Directories to back up (learned skills, memory, etc.)
BACKUP_DIRS = [
    "skills",
    "trajectories",
    "memory",
    ".hermes"
]

def log(msg: str, level: str = "INFO"):
    """Log with timestamp."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] [{level}] [GITHUB-SYNC] {msg}", flush=True)

def get_file_sha(content: bytes) -> str:
    """Get SHA1 hash of content (GitHub's format)."""
    return hashlib.sha1(content).hexdigest()

def file_exists_on_github(file_path: str) -> tuple:
    """Check if file exists on GitHub. Returns (exists, sha, content)."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return False, None, None

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("sha"), data.get("content")
        return False, None, None
    except Exception as e:
        log(f"Error checking file on GitHub: {e}", "WARN")
        return False, None, None

def push_file_to_github(file_path: str, content: str, message: str, sha: str = None) -> bool:
    """Push a file to GitHub. Returns True if successful."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return False

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    payload = {
        "message": message,
        "content": content,  # Base64 encoded
        "committer": {
            "name": "Hermes Bot",
            "email": "hermes@railway.local"
        }
    }

    if sha:
        payload["sha"] = sha  # For updates

    try:
        response = requests.put(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [201, 200]:
            return True
        else:
            log(f"GitHub API error {response.status_code}: {response.text}", "WARN")
            return False
    except Exception as e:
        log(f"Error pushing to GitHub: {e}", "WARN")
        return False

def sync_directory_to_github(local_dir: str, github_path: str) -> int:
    """Sync all files in a directory to GitHub. Returns number of files synced."""
    synced = 0
    local_path = Path(HERMES_HOME) / local_dir

    if not local_path.exists():
        log(f"Directory not found: {local_path}")
        return 0

    for file_path in local_path.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip large files and certain types
        if file_path.stat().st_size > 1_000_000:  # 1MB
            continue

        if file_path.suffix in [".pyc", ".so", ".dll", ".exe"]:
            continue

        try:
            # Read file content
            with open(file_path, "rb") as f:
                content = f.read()

            # Convert to base64
            import base64
            content_b64 = base64.b64encode(content).decode()

            # Construct GitHub path
            relative_path = file_path.relative_to(HERMES_HOME)
            gh_file_path = f"{github_path}/{relative_path}".replace("\\", "/")

            # Check if exists and get SHA
            exists, sha, _ = file_exists_on_github(gh_file_path)

            # Only push if changed
            if exists:
                existing_sha = sha
                new_sha = get_file_sha(content)
                if existing_sha == new_sha:
                    continue  # No change

            # Push to GitHub
            commit_msg = f"Hermes: backup {relative_path}"
            if push_file_to_github(gh_file_path, content_b64, commit_msg, sha=sha):
                synced += 1
                log(f"Synced: {gh_file_path}")

        except Exception as e:
            log(f"Error syncing {file_path}: {e}", "WARN")

    return synced

def main():
    """Main daemon loop."""
    log("Starting GitHub sync daemon")
    log(f"HERMES_HOME: {HERMES_HOME}")
    log(f"GitHub Repo: {GITHUB_REPO}")
    log(f"Sync interval: {SYNC_INTERVAL}s ({SYNC_INTERVAL//60}m)")

    if not GITHUB_TOKEN or not GITHUB_REPO:
        log("GITHUB_TOKEN or GITHUB_REPO not set - skipping sync", "WARN")
        return

    next_sync = time.time()

    try:
        while True:
            now = time.time()
            if now >= next_sync:
                try:
                    total_synced = 0
                    for backup_dir in BACKUP_DIRS:
                        github_path = "Core_Platform_Code/skills" if backup_dir == "skills" else backup_dir
                        synced = sync_directory_to_github(backup_dir, github_path)
                        if synced > 0:
                            log(f"Synced {synced} files from {backup_dir}")
                            total_synced += synced

                    if total_synced == 0:
                        log("No changes to sync")
                    else:
                        log(f"Total synced: {total_synced} files")

                except Exception as e:
                    log(f"Error during sync: {e}", "ERROR")

                next_sync = now + SYNC_INTERVAL

            time.sleep(10)

    except KeyboardInterrupt:
        log("Daemon shutting down")
    except Exception as e:
        log(f"Fatal error: {e}", "ERROR")

if __name__ == "__main__":
    main()
