"""Thin client for the Vault backend REST API."""

import logging

import requests

logger = logging.getLogger(__name__)


class BackendClient:
    """Wrapper around the backend endpoints the automation jobs rely on."""

    def __init__(self, base_url: str, timeout: int = 60):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def get_stocks(self) -> list:
        """Return the full stock watchlist."""
        response = requests.get(f'{self.base_url}/stocks/', timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def post_bulk_prices(self, source: str, trading_date: str, prices: list) -> dict:
        """Push a batch of prices to the backend bulk-update endpoint."""
        payload = {
            'source': source,
            'date': trading_date,
            'prices': prices,
        }
        response = requests.post(
            f'{self.base_url}/prices/bulk',
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def health(self) -> bool:
        """Best-effort backend reachability check."""
        root = self.base_url[:-4] if self.base_url.endswith('/api') else self.base_url
        try:
            response = requests.get(f'{root}/health', timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
