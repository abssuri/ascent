"""The core game logic stays independent of the Textual UI layer.

Importing ``ascent.core`` must not pull in ``textual``. The one-way dependency
(ui depends on core, never the reverse) keeps the game logic headless and
testable. The check runs in a fresh subprocess so an unrelated import elsewhere
in the test session cannot mask a real violation.
"""

import subprocess
import sys


def test_importing_core_does_not_load_textual() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import ascent.core, sys; assert 'textual' not in sys.modules",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
