"""The ascent package exposes a runnable command-line entry point."""

import re
import subprocess
import sys


def test_version_flag_prints_version_and_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "ascent", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert re.search(r"\d+\.\d+", result.stdout), result.stdout
