"""Environment-driven configuration for the automation service."""

import os


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _series_env(name: str, default: str) -> tuple:
    raw = os.environ.get(name, default)
    return tuple(part.strip().upper() for part in raw.split(',') if part.strip())


class Config:
    """Runtime configuration (override with environment variables)."""

    # --- Vault backend -----------------------------------------------------
    # Stage 1 (local): http://localhost:5000/api
    # Stage 2 (compose): http://backend:5000/api
    BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5000/api').rstrip('/')
    BACKEND_TIMEOUT = _int_env('BACKEND_TIMEOUT', 60)

    # --- HTTP service ------------------------------------------------------
    HOST = os.environ.get('AUTOMATION_HOST', '0.0.0.0')
    PORT = _int_env('AUTOMATION_PORT', 8080)
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

    # --- Bhavcopy extraction ----------------------------------------------
    MAX_LOOKBACK_DAYS = _int_env('MAX_LOOKBACK_DAYS', 10)
    # Only send symbols present in the Vault watchlist ('matched'), or send
    # every parsed row and let the backend filter ('all').
    BULK_MODE = os.environ.get('BULK_MODE', 'matched').strip().lower()
    EQUITY_SERIES = _series_env('EQUITY_SERIES', 'EQ,BE')
    # Optional directory for a CSV audit artifact (symbol + close). Empty = off.
    ARTIFACTS_DIR = os.environ.get('ARTIFACTS_DIR', '').strip()

    # --- Scheduling (Stage 2) ---------------------------------------------
    ENABLE_SCHEDULE = _bool_env('ENABLE_SCHEDULE', False)
    RUN_TIME = os.environ.get('RUN_TIME', '18:30')
    STARTUP_DELAY_SECONDS = _int_env('STARTUP_DELAY_SECONDS', 60)
    TIMEZONE = os.environ.get('TZ', 'Asia/Kolkata')


config = Config()
