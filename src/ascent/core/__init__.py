"""Headless, deterministic game logic.

This package must never import ``textual`` (or any other UI library). The
dependency runs one way only: ``ascent.ui`` depends on ``ascent.core``, never
the reverse. A test in ``tests/core/test_layering.py`` enforces this.
"""
