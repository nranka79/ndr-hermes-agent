#!/usr/bin/env python3
"""
Background daemon for Hermes on Railway.
Periodically syncs learned skills from /data/hermes to GitHub.
Runs as a background process alongside the main Hermes gateway.
"""

import os
import subprocess
import time
import sys
from datetime import datetime

HERMES_HOME = os.environ.get("HERMES_HOME", "/data/hermes")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
SYNC_INTERVAL = 300  # 5 minutes (in seconds)

def log(msg: str, level: str = "INFO"):
    """Log messages with timestamp."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] [{level}] [GIT-SYNC-DAEMON] {msg}", flush=True)

def git_command(args: list, cwd: str = HERMES_HOME) -> tuple:
    """Execute a git command. Returns (success, output)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return (result.returncode == 0, result.stdout + result.stderr)
    except FileNotFoundError:
        return (False, "git command not found")
    except subprocess.TimeoutExpired:
        return (False, "git command timed out")
    except Exception as e:
        return (False, str(e))

def initialize_git_repo():
    """Initialize git repo if not already initialized."""
    if os.path.exists(os.path.join(HERMES_HOME, ".git")):
        return True

    log("Initializing git repository...")

    success, _ = git_command(["init"])
    if not success:
        log("Failed to initialize git repo", "ERROR")
        return False

    git_command(["config", "user.name", "Hermes Bot"])
    git_command(["config", "user.email", "hermes@railway.local"])

    if GITHUB_TOKEN and GITHUB_REPO:
        remote_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
        git_command(["remote", "add", "origin", remote_url])

    log("Git repository initialized")
    return True

def sync_to_github():
    """Check for changes and push to GitHub."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        log("Skipping sync: GITHUB_TOKEN or GITHUB_REPO not configured", "WARN")
        return

    # Check if there are changes
    success, output = git_command(["status", "--porcelain"])
    if not success:
        log(f"Failed to check git status: {output}", "ERROR")
        return

    if not output.strip():
        log("No changes to commit")
        return

    log("Found changes, preparing to push...")

    # Stage all changes
    success, _ = git_command(["add", "-A"])
    if not success:
        log("Failed to stage changes", "ERROR")
        return

    # Commit changes
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    commit_msg = f"Hermes: auto-sync from Railway {timestamp}"
    success, _ = git_command(["commit", "-m", commit_msg])
    if not success:
        log("No changes to commit (working directory clean)")
        return

    # Fetch latest from origin to avoid conflicts
    log("Fetching latest from GitHub...")
    git_command(["fetch", "origin", "main"])

    # Try to merge if there are remote changes
    git_command(["merge", "origin/main", "--no-edit"])

    # Push to GitHub
    log("Pushing to GitHub...")
    success, output = git_command(["push", "-u", "origin", "main"])

    if success:
        log("Successfully pushed to GitHub")
    else:
        # Don't treat push failures as fatal - network might be temporarily down
        log(f"Push failed (will retry later): {output[:200]}", "WARN")

def main():
    """Main daemon loop."""
    log("Starting Hermes git sync daemon")
    log(f"HERMES_HOME: {HERMES_HOME}")
    log(f"GitHub Repo: {GITHUB_REPO}")
    log(f"Sync interval: {SYNC_INTERVAL}s ({SYNC_INTERVAL//60}m)")

    # Ensure HERMES_HOME exists
    os.makedirs(HERMES_HOME, exist_ok=True)

    # Initialize git repo
    if not initialize_git_repo():
        log("Failed to initialize git repo, continuing without sync", "WARN")

    # Main loop
    next_sync = time.time()

    try:
        while True:
            now = time.time()
            if now >= next_sync:
                try:
                    sync_to_github()
                except Exception as e:
                    log(f"Unexpected error during sync: {e}", "ERROR")

                next_sync = now + SYNC_INTERVAL

            # Sleep for 10 seconds before checking again
            time.sleep(10)

    except KeyboardInterrupt:
        log("Daemon shutting down (KeyboardInterrupt)")
        sys.exit(0)
    except Exception as e:
        log(f"Fatal error in daemon loop: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
