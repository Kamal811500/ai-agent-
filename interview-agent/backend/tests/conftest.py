"""
pytest configuration and fixtures.
"""
import sys
import os
from pathlib import Path

# Add backend directory to path so imports work
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set minimal environment variables for testing
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key-for-testing-only")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "WARNING")
