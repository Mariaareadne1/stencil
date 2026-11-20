"""Shared setup for the API smoke tests.

Run from the repository root:  python -m pytest apps/api/tests
"""
from __future__ import annotations

import os

# Must be set before apps.api.services.pipeline is imported: it picks the
# stub or real services at import time. Tests never call paid providers.
os.environ.setdefault("USE_STUBS", "true")
