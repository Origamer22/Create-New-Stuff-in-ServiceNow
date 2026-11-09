import os
import sys

# Ensure servicenow_creator/ is importable under both `python -m unittest` and `pytest`
_CREATOR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _CREATOR_DIR not in sys.path:
    sys.path.insert(0, _CREATOR_DIR)

