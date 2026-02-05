"""Vercel serverless function entry point for Phase2 API.

This module re-exports the FastAPI app from the main application.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the FastAPI app from the main module
from app.main import app

# Re-export for Vercel
__all__ = ["app"]
