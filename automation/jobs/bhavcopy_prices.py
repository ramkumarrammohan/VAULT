"""NSE bhavcopy -> Vault price sync job."""

import csv
import logging
import os
from datetime import date, datetime, timezone

from ..backend_client import BackendClient
from ..config import config
from ..nse import bhavcopy
from .base import Job

logger = logging.getLogger(__name__)

SOURCE = 'nse-bhavcopy'


def _base_symbol(symbol: str) -> str:
    """Strip the Yahoo exchange suffix (RELIANCE.NS -> RELIANCE)."""
    sym = (symbol or '').strip().upper()
    for suffix in ('.NS', '.BO'):
        if sym.endswith(suffix):
            return sym[: -len(suffix)]
    return sym


def _parse_date(value):
    """Accept a ``date``, ``datetime`` or ``YYYY-MM-DD`` string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), '%Y-%m-%d').date()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace('+00:00', 'Z')


class BhavcopyPriceSyncJob(Job):
    """Download the latest NSE bhavcopy and push INR close prices to Vault.

    Only symbols already tracked in Vault are sent (``BULK_MODE=matched``), so
    the payload stays tiny. The backend independently enforces that only INR
    stocks are updated, so USD tickers are never touched.
    """

    name = 'bhavcopy'
    description = 'Sync NSE bhavcopy close prices for tracked INR stocks'

    def __init__(self, backend: BackendClient | None = None):
        self._backend = backend

    @property
    def backend(self) -> BackendClient:
        return self._backend or BackendClient(
            config.BACKEND_URL, config.BACKEND_TIMEOUT
        )

    # -- internals ----------------------------------------------------------
    def _load_watchlist(self) -> dict:
        """Map base symbol -> tracked stock dicts."""
        watchlist = {}
        for stock in self.backend.get_stocks():
            watchlist.setdefault(_base_symbol(stock.get('symbol')), []).append(stock)
        return watchlist

    def _write_artifact(self, trading_date, prices) -> str | None:
        """Optionally persist a CSV audit artifact; returns its path."""
        if not config.ARTIFACTS_DIR or not prices:
            return None
        os.makedirs(config.ARTIFACTS_DIR, exist_ok=True)
        path = os.path.join(
            config.ARTIFACTS_DIR, f'bhavcopy_prices_{trading_date.isoformat()}.csv'
        )
        with open(path, 'w', newline='', encoding='utf-8') as handle:
            writer = csv.writer(handle)
            writer.writerow(['DATE', 'SYMBOL', 'CLOSE_PRICE'])
            for row in prices:
                writer.writerow([trading_date.strftime('%d-%m-%Y'), row['symbol'], row['price']])
        logger.info("wrote artifact %s", path)
        return path

    # -- job entry point ----------------------------------------------------
    def run(self, trading_date=None, lookback_days=None, downloader=None, now=None) -> dict:
        started_at = _utcnow()
        requested_date = _parse_date(trading_date)

        # 1. Watchlist (used to decide which symbols to send).
        bulk_mode = config.BULK_MODE
        watchlist = {}
        try:
            watchlist = self._load_watchlist()
            logger.info("loaded watchlist with %d symbol(s)", len(watchlist))
        except Exception as exc:
            if bulk_mode == 'matched':
                logger.warning(
                    "could not load watchlist (%s); falling back to BULK_MODE=all", exc
                )
                bulk_mode = 'all'
            else:
                raise

        # 2. Locate + download the latest bhavcopy.
        resolved_date, zip_data = bhavcopy.find_latest_bhavcopy(
            max_days=lookback_days or config.MAX_LOOKBACK_DAYS,
            start_date=requested_date,
            now=now,
            downloader=downloader,
        )

        # 3. Parse all rows (symbol + close).
        rows = bhavcopy.extract_prices(
            zip_data, resolved_date, equity_series=config.EQUITY_SERIES
        )

        # 4. Keep only the symbols Vault tracks (unless BULK_MODE=all).
        if bulk_mode == 'all':
            prices = rows
        else:
            prices = [row for row in rows if _base_symbol(row['symbol']) in watchlist]

        # Collapse duplicates (e.g. same symbol in EQ + BE series); last wins.
        deduped = {}
        for row in prices:
            deduped[_base_symbol(row['symbol'])] = row
        prices = list(deduped.values())

        artifact = self._write_artifact(resolved_date, prices)

        report = {
            'job': self.name,
            'status': 'success',
            'source': SOURCE,
            'trading_date': resolved_date.isoformat(),
            'bulk_mode': bulk_mode,
            'watchlist_symbols': len(watchlist),
            'bhavcopy_rows': len(rows),
            'sent_symbols': len(prices),
            'symbols_not_tracked': max(len(rows) - len(prices), 0) if bulk_mode == 'matched' else 0,
            'artifact': artifact,
            'started_at': _iso(started_at),
        }

        # 5. Push to the backend (skip a pointless round-trip when empty).
        if not prices:
            report['backend'] = None
            report['message'] = (
                'No tracked symbols found in the bhavcopy - nothing to update.'
            )
        else:
            report['backend'] = self.backend.post_bulk_prices(
                SOURCE, resolved_date.isoformat(), prices
            )

        finished_at = _utcnow()
        report['finished_at'] = _iso(finished_at)
        report['duration_seconds'] = round((finished_at - started_at).total_seconds(), 2)
        return report
