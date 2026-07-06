"""Grade a candidate solution by running a test file against it.

We copy the test file into the workspace and run it there, so Python's
script-directory-on-sys.path rule makes `import solution` resolve to
<workspace>/solution.py (the file under test) rather than any solution.py that
happens to sit next to the test's original location. Runs in a subprocess with a
wall-clock timeout so a bad fix that loops forever can't stall the run.
"""
import os
import shutil
import subprocess
import sys

_RUNNER = "_run_test.py"


def run_test_file(workspace, test_file, timeout=20):
    """Return (passed: bool, log: str)."""
    dst = os.path.join(workspace, _RUNNER)
    shutil.copy(test_file, dst)
    try:
        r = subprocess.run(
            [sys.executable, _RUNNER],
            cwd=workspace,
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    finally:
        try:
            os.remove(dst)
        except OSError:
            pass
    return (r.returncode == 0 and "PASS" in r.stdout), (r.stdout + r.stderr)
