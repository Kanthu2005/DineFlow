import os
import sys

# Ensure the project root directory is in sys.path for Vercel serverless execution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.main import app

__all__ = ["app"]
