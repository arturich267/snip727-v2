"""Test configuration and fixtures."""
import sys
import os
from pathlib import Path

# Add src to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Test configuration
TEST_DATABASE_URL = "postgresql+asyncpg://snip727:snip727@localhost:5432/snip727_test"
TEST_REDIS_URL = "redis://localhost:6379/1"