"""
Mutual fund NAV provider.

Fetches Indian mutual fund NAV data (net asset value per unit) from mfapi.in,
an unofficial REST mirror of the daily AMFI NAV publication. yfinance does not
reliably cover Indian mutual fund schemes, so funds use this dedicated source.

Endpoints used:
  GET https://api.mfapi.in/mf          -> full scheme list [{schemeCode, schemeName}, ...]
  GET https://api.mfapi.in/mf/{code}   -> {"meta": {...}, "data": [{"date","nav"}, ...]}
"""
import json
import urllib.request
import urllib.error
from datetime import datetime

MFAPI_BASE = 'https://api.mfapi.in/mf'
DEFAULT_TIMEOUT = 20


class NavError(Exception):
    """Raised when NAV data cannot be fetched from the provider."""

    def __init__(self, message, status_code=500, hint=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.hint = hint


def _http_get_json(url: str):
    """GET a JSON resource, raising a mapped NavError on any failure."""
    req = urllib.request.Request(url, headers={'User-Agent': 'vault-portfolio-tracker/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            if resp.status != 200:
                raise NavError(
                    f'NAV service returned HTTP {resp.status}', status_code=503,
                    hint='The NAV provider may be temporarily unavailable. Please try again later.'
                )
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise NavError('Scheme not found on NAV provider.', status_code=404,
                           hint='Verify the AMFI scheme code is correct.')
        if e.code == 429:
            raise NavError('NAV provider rate limit reached. Please wait a minute.',
                           status_code=429,
                           hint='Try again after a short pause.')
        raise NavError(f'NAV provider returned HTTP {e.code}', status_code=503,
                       hint='The NAV provider may be temporarily unavailable.')
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise NavError('Unable to connect to the NAV provider.',
                       status_code=503,
                       hint='Check your internet connection and try again.') from e
    except (json.JSONDecodeError, ValueError) as e:
        raise NavError('Unexpected response from NAV provider.', status_code=502) from e


def _parse_date(day_month_year: str) -> datetime:
    """Parse mfapi date format 'dd-mm-yyyy' -> datetime."""
    return datetime.strptime(day_month_year.strip(), '%d-%m-%Y')


def _format_iso(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%d')


def search_schemes(query: str, limit: int = 50):
    """Search the AMFI scheme list by name substring."""
    try:
        payload = _http_get_json(f'{MFAPI_BASE}')
    except NavError:
        raise
    if not isinstance(payload, list):
        raise NavError('Unexpected scheme list format from NAV provider.', status_code=502)

    q = (query or '').strip().lower()
    results = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = str(item.get('schemeName') or '')
        code = str(item.get('schemeCode') or '')
        if q and q not in name.lower():
            continue
        results.append({'scheme_code': code, 'scheme_name': name})
        if len(results) >= limit:
            break
    return results


def fetch_scheme_data(scheme_code: str):
    """Fetch meta + full NAV history for a scheme code.

    Returns {'meta': {...}, 'history': [{'date': 'YYYY-MM-DD', 'nav': float}, ...]}
    sorted oldest -> newest. Raises NavError when not found / empty.
    """
    code = str(scheme_code or '').strip()
    if not code:
        raise NavError('Scheme code is required.', status_code=400)
    payload = _http_get_json(f'{MFAPI_BASE}/{code}')

    meta = payload.get('meta') or {}
    raw_data = payload.get('data') or []
    if not raw_data:
        raise NavError('No NAV history received for this scheme.', status_code=404,
                       hint='The scheme code may be invalid or has no published NAV yet.')

    history = []
    for row in raw_data:
        try:
            nav = float(row['nav'])
            day = _parse_date(row['date'])
        except (KeyError, TypeError, ValueError):
            continue
        history.append({'date': _format_iso(day), 'nav': nav})

    history.sort(key=lambda x: x['date'])
    if not history:
        raise NavError('No valid NAV history received for this scheme.', status_code=404)

    return {'meta': meta, 'history': history}


def fetch_latest_nav(scheme_code: str):
    """Return the most recent (nav, iso_date) for a scheme code."""
    data = fetch_scheme_data(scheme_code)
    latest = data['history'][-1]
    return latest['nav'], latest['date']


def fetch_nav_on(scheme_code: str, target_date, fallback='previous'):
    """Return (nav, iso_date) for the NAV applicable on target_date.

    - fallback='previous' (default): the latest NAV on or before target_date.
    - fallback='next': the earliest NAV on or after target_date.
    Returns None when no suitable NAV exists in the history.
    """
    data = fetch_scheme_data(scheme_code)
    target = target_date if isinstance(target_date, datetime) else _parse_iso_or_dmy(target_date)
    target_key = target.strftime('%Y-%m-%d')

    if fallback == 'next':
        for row in data['history']:
            if row['date'] >= target_key:
                return row['nav'], row['date']
        return None
    # previous
    prev = None
    for row in data['history']:
        if row['date'] <= target_key:
            prev = row
        else:
            break
    if prev is not None:
        return prev['nav'], prev['date']
    # nothing before target -> fall back to earliest available
    earliest = data['history'][0]
    return earliest['nav'], earliest['date']


def _parse_iso_or_dmy(value) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise NavError('Invalid date format for NAV lookup.', status_code=400)
