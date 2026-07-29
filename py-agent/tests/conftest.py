import sys
from pathlib import Path

# Ensure the py-agent package root is importable when tests are run from the repo root.
PY_AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(PY_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_AGENT_ROOT))
