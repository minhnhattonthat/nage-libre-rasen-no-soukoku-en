"""check.py: the repo's one-command check (tests + text lint). The pre-commit hook runs it; exit code gates the commit.

    python -X utf8 tools/check.py"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    # no faulthandler: it dumps a stack for the access violation unicorn's mem_map raises and handles itself on Windows
    tests = subprocess.call([sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:faulthandler",
                             str(ROOT / "tests")], cwd=ROOT)
    lint = subprocess.call([sys.executable, "-X", "utf8", str(ROOT / "tools/lint.py")], cwd=ROOT)
    sys.exit(1 if tests or lint else 0)
