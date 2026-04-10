import os
import sys
from pathlib import Path


def ensure_minisweagent_on_path(repo_root: Path = None):
    """
    Ensures that the mini-swe-agent submodule is in the Python path.
    
    Args:
        repo_root: The root directory of the Hermes repo. If not provided,
                   the directory containing this file is used as fallback.
    
    Called by terminal_tool.py as:
        ensure_minisweagent_on_path(Path(__file__).resolve().parent.parent)
    """
    if repo_root is None:
        root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    else:
        root_dir = Path(repo_root)
    
    miniswe_dir = root_dir / "mini-swe-agent"
    
    if miniswe_dir.exists():
        miniswe_str = str(miniswe_dir)
        if miniswe_str not in sys.path:
            sys.path.insert(0, miniswe_str)
        # Also add the src directory if it exists (some layouts use src/)
        src_dir = miniswe_dir / "src"
        if src_dir.exists():
            src_str = str(src_dir)
            if src_str not in sys.path:
                sys.path.insert(0, src_str)
    # If mini-swe-agent doesn't exist, the terminal tool will fail gracefully
    # when it actually tries to import from it.
