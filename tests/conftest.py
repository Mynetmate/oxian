import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent

# Ensure the repository root is in sys.path
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import oxian_py as oxian_module
sys.modules["oxian"] = oxian_module
