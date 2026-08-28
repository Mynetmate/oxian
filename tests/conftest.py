import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent

# Ensure the repository root is in sys.path
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Map root package as oxian_py and oxian with proper __path__ for subpackage resolution
import __init__ as oxian_module

oxian_module.__path__ = [str(repo_root)]
oxian_module.__package__ = "oxian_py"

sys.modules["oxian_py"] = oxian_module
sys.modules["oxian"] = oxian_module
