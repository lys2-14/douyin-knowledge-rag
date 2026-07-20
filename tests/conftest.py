"""Shared fixtures for tests."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Enable async tests
pytest_plugins = ["pytest_asyncio"]
