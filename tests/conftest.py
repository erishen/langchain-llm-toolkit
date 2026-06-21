"""Pytest configuration for langchain-llm-toolkit tests."""

import os

# Set INTERNAL_API_KEY for API tests that need auth bypass
os.environ.setdefault("INTERNAL_API_KEY", "test-key-12345")
