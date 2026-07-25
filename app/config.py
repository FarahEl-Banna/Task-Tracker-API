"""
Minimal environment configuration loader.

Loads variables from a local .env file (if present) using python-dotenv,
and exposes them as simple module-level constants. Kept intentionally
small: no settings framework, no validation layer, no database config.
"""

import os

from dotenv import load_dotenv

load_dotenv()

APP_ENV: str = os.getenv("APP_ENV", "development")
PORT: int = int(os.getenv("PORT", "8000"))
