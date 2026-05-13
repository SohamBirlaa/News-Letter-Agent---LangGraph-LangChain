"""
conftest.py — shared pytest configuration and fixtures.
Placed in the tests/ folder so pytest picks it up automatically.
"""

import os
import sys
import pytest

# ── Add project root to path so all imports work ───────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── Set required env vars before any project module imports ─
os.environ.setdefault("TAVILY_AP_KEY", "test-placeholder-key")