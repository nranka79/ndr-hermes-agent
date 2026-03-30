import os
import sys

def ensure_minisweagent_on_path():
    """
    Ensures that the mini-swe-agent submodule is in the Python path.
    This is required for the terminal tool to function correctly.
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    miniswe_dir = os.path.join(root_dir, "mini-swe-agent")
    
    if os.path.exists(miniswe_dir):
        if miniswe_dir not in sys.path:
            sys.path.insert(0, miniswe_dir)
            # Also add the src directory if it exists
            src_dir = os.path.join(miniswe_dir, "src")
            if os.path.exists(src_dir):
                sys.path.insert(0, src_dir)
    else:
        # If directory doesn't exist, we can't add it.
        # The terminal tool will handle the actual error when it tries to use it.
        pass
