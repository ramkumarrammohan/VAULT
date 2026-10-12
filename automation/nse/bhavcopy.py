"""NSE bhavcopy download and parsing.

Adapted from the standalone extractor script. The original behaviour is
preserved:

  * same NSE archive URL (``BhavCopy_NSE_CM_0_0_0_<date>_F_0000.csv.zip``)
  * same browser-style request headers
  * streaming download with a basic ZIP ("PK") validation
  * 5:00 PM IST cutoff when picking the start date
  * up to N calendar days of walk-back to cover weekends / NSE holidays
  * ``TckrSymb`` / ``ClsPric`` column parsing

Differences for the automation use case:

  * progress ``print`` calls are replaced with :mod:`logging`
  * the parsed result is returned as data (list of dicts) instead of being
    written to a CSV file; callers may persist a CSV artifact themselves
  * an optional equity-series filter (``SctySrs`` in {EQ, BE}) drops
    non-equity instruments before returning
"""

import io
import logging
import zipfile
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import requests

logger = logging.getLogger(__name__)

NSE_URL = (
    "https://nsearchives.nseindia.com/content/cm/"
    "BhavCopy_NSE_CM_0_0_0_{date}_F_0000.csv.zip"
)

#: The bhavcopy for a trading day is published after market close (5 PM IST).
MARKET_CLOSE_HOUR = 17

IST = ZoneInfo("Asia/Kolkata")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/154.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/",
}

SYMBOL_COL = "TckrSymb"
CLOSE_COL = "ClsPric"
SERIES_COL = "SctySrs"

DEFAULT_EQUITY_SERIES = ("EQ", "BE")
DEFAULT_MAX_LOOKBACK_DAYS = 10


def get_start_date(now: datetime | None = None):
    """Return the first date to try when searching for a bhavcopy.

    After the 5 PM IST cutoff, today's report is attempted; before it, the
    previous calendar day.
    """
    now = now or datetime.now(IST)
    cutoff = now.replace(
        hour=MARKET_CLOSE_HOUR,
        minute=0,
        second=0,
        microsecond=0,
    )
    if now >= cutoff:
        return now.date()
    return now.date() - timedelta(days=1)


def download_bhavcopy(trading_date, timeout: int = 30, session=None) -> bytes | None:
    """Download the NSE bhavcopy ZIP for ``trading_date``.

    Returns the raw ZIP bytes, or ``None`` when the report is unavailable
    (weekend/holiday, not yet published, or a transient failure).
    """
    date_str = trading_date.strftime("%Y%m%d")
    url = NSE_URL.format(date=date_str)
    http = session or requests

    try:
        response = http.get(url, headers=HEADERS, timeout=timeout, stream=True)

        if response.status_code != 200:
            logger.info("bhavcopy %s unavailable (HTTP %s)", date_str, response.status_code)
            return None

        chunks = []
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                chunks.append(chunk)
        data = b"".join(chunks)

    except requests.RequestException as exc:
        logger.warning("bhavcopy %s download failed: %s", date_str, exc)
        return None

    # Basic ZIP validation - NSE sometimes serves an HTML error page.
    if not data.startswith(b"PK"):
        logger.warning("bhavcopy %s is not a valid ZIP", date_str)
        return None

    logger.info("downloaded bhavcopy %s (%d bytes)", date_str, len(data))
    return data


def find_latest_bhavcopy(
    max_days: int | None = None,
    start_date=None,
    now: datetime | None = None,
    downloader=None,
):
    """Find the most recent available bhavcopy.

    Walks backwards from ``start_date`` (or :func:`get_start_date`), skipping
    weekends, for up to ``max_days`` iterations.

    Returns:
        (trading_date, zip_data)

    Raises:
        RuntimeError: when no report is found within ``max_days``.
    """
    max_days = max_days or DEFAULT_MAX_LOOKBACK_DAYS
    download = downloader or download_bhavcopy
    current_date = start_date or get_start_date(now)
    attempted = []

    for _ in range(max_days):
        # Skip Saturday and Sunday.
        if current_date.weekday() >= 5:
            current_date -= timedelta(days=1)
            continue

        attempted.append(current_date)
        logger.info("trying bhavcopy for %s", current_date.isoformat())

        zip_data = download(current_date)
        if zip_data is not None:
            logger.info("using bhavcopy for %s", current_date.isoformat())
            return current_date, zip_data

        current_date -= timedelta(days=1)

    tried = ", ".join(d.isoformat() for d in attempted) or "no weekdays"
    raise RuntimeError(
        f"No NSE bhavcopy found within the last {max_days} days (tried: {tried})"
    )


def _read_bhavcopy_dataframe(zip_data: bytes) -> pd.DataFrame:
    """Extract the first CSV inside the bhavcopy ZIP as a DataFrame."""
    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        csv_files = [name for name in z.namelist() if name.lower().endswith(".csv")]
        if not csv_files:
            raise RuntimeError("No CSV found inside NSE bhavcopy ZIP")

        with z.open(csv_files[0]) as csv_file:
            return pd.read_csv(csv_file)


def extract_prices(
    zip_data: bytes,
    trading_date=None,
    equity_series=DEFAULT_EQUITY_SERIES,
) -> list[dict]:
    """Parse a bhavcopy ZIP into a list of ``{"symbol", "price"}`` dicts.

    Args:
        zip_data: raw ZIP bytes from :func:`download_bhavcopy`.
        trading_date: trading date the bhavcopy belongs to (used for logging).
        equity_series: security series to keep (e.g. ``("EQ", "BE")``). Pass
            ``None`` or an empty tuple to keep every row. Ignored when the
            bhavcopy has no series column.

    Raises:
        RuntimeError: if the expected columns are missing.
    """
    df = _read_bhavcopy_dataframe(zip_data)

    for column in (SYMBOL_COL, CLOSE_COL):
        if column not in df.columns:
            raise RuntimeError(f"Column '{column}' not found in bhavcopy")

    # Keep only the columns we need so the series mask stays index-aligned.
    result = df[[SYMBOL_COL, CLOSE_COL]].copy()
    result.columns = ["SYMBOL", "CLOSE_PRICE"]

    filtered_non_equity = 0
    if equity_series and SERIES_COL in df.columns:
        series = {str(item).upper() for item in equity_series}
        mask = df[SERIES_COL].astype(str).str.strip().str.upper().isin(series)
        filtered_non_equity = int((~mask).sum())
        result = result[mask]

    result = result.dropna(subset=["SYMBOL", "CLOSE_PRICE"])
    result["SYMBOL"] = result["SYMBOL"].astype(str).str.strip()
    result["CLOSE_PRICE"] = pd.to_numeric(result["CLOSE_PRICE"], errors="coerce")
    result = result.dropna(subset=["CLOSE_PRICE"])
    result = result[result["SYMBOL"] != ""]

    logger.info(
        "parsed %d rows for %s (dropped %d non-equity, %d without close)",
        len(result),
        trading_date.isoformat() if trading_date else "unknown date",
        filtered_non_equity,
        len(df) - len(result),
    )

    return [
        {"symbol": row.SYMBOL, "price": round(float(row.CLOSE_PRICE), 2)}
        for row in result.itertuples(index=False)
    ]
