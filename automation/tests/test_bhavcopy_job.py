"""Tests for the bhavcopy price-sync job."""

import unittest
from datetime import date

from automation import config as config_module
from automation.jobs.bhavcopy_prices import BhavcopyPriceSyncJob, _base_symbol
from automation.tests.test_bhavcopy import make_zip

TRADING_DATE = date(2026, 10, 9)

BHAVCOPY_ROWS = [
    {'TckrSymb': 'RELIANCE', 'SctySrs': 'EQ', 'ClsPric': 2450.50},
    {'TckrSymb': 'TCS', 'SctySrs': 'EQ', 'ClsPric': 3567.20},
    {'TckrSymb': 'NOTTRACKED', 'SctySrs': 'EQ', 'ClsPric': 11.00},
]

WATCHLIST = [
    {'symbol': 'RELIANCE.NS', 'currency': 'INR', 'exchange': 'NSE'},
    {'symbol': 'TCS.NS', 'currency': 'INR', 'exchange': 'NSE'},
    {'symbol': 'AAPL', 'currency': 'USD', 'exchange': 'NASDAQ'},
]


class FakeBackend:
    """Records the bulk payload instead of calling the real API."""

    def __init__(self, stocks=None, fail_watchlist=False):
        self.stocks = stocks if stocks is not None else WATCHLIST
        self.fail_watchlist = fail_watchlist
        self.posted = None

    def get_stocks(self):
        if self.fail_watchlist:
            raise RuntimeError('backend unavailable')
        return self.stocks

    def post_bulk_prices(self, source, trading_date, prices):
        self.posted = {'source': source, 'date': trading_date, 'prices': prices}
        return {
            'updated': [p['symbol'] for p in prices],
            'updated_count': len(prices),
            'skipped': [],
            'unmatched': [],
        }


class BhavcopyPriceSyncJobTests(unittest.TestCase):
    def setUp(self):
        self._saved_bulk_mode = config_module.config.BULK_MODE
        config_module.config.BULK_MODE = 'matched'

    def tearDown(self):
        config_module.config.BULK_MODE = self._saved_bulk_mode

    def _run(self, backend=None, rows=None, **kwargs):
        backend = backend or FakeBackend()
        job = BhavcopyPriceSyncJob(backend=backend)
        report = job.run(
            trading_date='2026-10-09',
            downloader=lambda day: make_zip(rows or BHAVCOPY_ROWS),
            **kwargs,
        )
        return report, backend

    def test_matched_mode_sends_only_tracked_symbols(self):
        report, backend = self._run()

        sent = [row['symbol'] for row in backend.posted['prices']]
        self.assertEqual(sorted(sent), ['RELIANCE', 'TCS'])
        self.assertEqual(backend.posted['source'], 'nse-bhavcopy')
        self.assertEqual(backend.posted['date'], '2026-10-09')
        self.assertEqual(report['status'], 'success')
        self.assertEqual(report['watchlist_symbols'], 3)
        self.assertEqual(report['bhavcopy_rows'], 3)
        self.assertEqual(report['sent_symbols'], 2)

    def test_all_mode_sends_every_row(self):
        config_module.config.BULK_MODE = 'all'
        report, backend = self._run()

        sent = [row['symbol'] for row in backend.posted['prices']]
        self.assertEqual(sorted(sent), ['NOTTRACKED', 'RELIANCE', 'TCS'])
        self.assertEqual(report['bulk_mode'], 'all')

    def test_no_tracked_symbols_skips_backend_post(self):
        backend = FakeBackend(stocks=[{'symbol': 'ZZZZ.NS', 'currency': 'INR'}])
        report, backend = self._run(backend=backend)

        self.assertIsNone(backend.posted)
        self.assertIsNone(report['backend'])
        self.assertEqual(report['sent_symbols'], 0)

    def test_watchlist_failure_falls_back_to_all(self):
        backend = FakeBackend(fail_watchlist=True)
        report, backend = self._run(backend=backend)

        sent = [row['symbol'] for row in backend.posted['prices']]
        self.assertEqual(sorted(sent), ['NOTTRACKED', 'RELIANCE', 'TCS'])
        self.assertEqual(report['bulk_mode'], 'all')

    def test_duplicate_symbols_are_deduplicated(self):
        rows = [
            {'TckrSymb': 'RELIANCE', 'SctySrs': 'EQ', 'ClsPric': 2450.50},
            {'TckrSymb': 'RELIANCE', 'SctySrs': 'BE', 'ClsPric': 2449.10},
        ]
        _, backend = self._run(rows=rows)

        self.assertEqual(len(backend.posted['prices']), 1)
        self.assertEqual(backend.posted['prices'][0]['price'], 2449.10)

    def test_report_contains_timing_and_date(self):
        report, _ = self._run()
        self.assertEqual(report['trading_date'], '2026-10-09')
        self.assertIn('duration_seconds', report)
        self.assertIn('finished_at', report)


class BaseSymbolTests(unittest.TestCase):
    def test_strips_yahoo_suffixes(self):
        self.assertEqual(_base_symbol('reliance.ns'), 'RELIANCE')
        self.assertEqual(_base_symbol('TCS.BO'), 'TCS')
        self.assertEqual(_base_symbol('AAPL'), 'AAPL')
        self.assertEqual(_base_symbol(None), '')


if __name__ == '__main__':
    unittest.main()
