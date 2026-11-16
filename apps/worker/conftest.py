import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

pytest_plugins = ["mistralai.workflows.testing.fixtures"]
