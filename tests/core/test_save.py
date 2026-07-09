"""Versioned save and load of a run.

A run serialises to a JSON-safe dict tagged with a save version and reloads to an
identical run. A save from an unrecognised version is refused rather than
silently misread.
"""

import json

import pytest

from ascent.core.run import Run
from ascent.core.save import SaveVersionError, from_dict, to_dict


def test_run_round_trips_through_save_and_load_identically() -> None:
    run = Run.from_seed(1)
    run.clear_node()

    saved = json.dumps(to_dict(run))
    loaded = from_dict(json.loads(saved))

    assert to_dict(loaded) == to_dict(run)


def test_loading_an_unknown_save_version_raises() -> None:
    with pytest.raises(SaveVersionError):
        from_dict({"save_version": 999})
