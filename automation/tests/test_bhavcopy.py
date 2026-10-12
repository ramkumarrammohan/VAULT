"""Tests for the adapted NSE bhavcopy extractor."""

import io
import unittest
import zipfile
from datetime import date, datetime

import pandas as pd

from automation.nse import bhavcopy


def make_zip(rows, columns=None) -> bytes:
    """Build an in-memory bhavcopy ZIP from a list of dicts."""
    frame = pd.DataFrame(rows, columns=columns)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('BhavCopy_NSE_CM_0_0_0_test.csv', frame.to_csv(index=False))
    return buffer.getvalue()


SAMPLE_ROWS = [
    {'TckrSymb': 'RELIANCE', 'SctySrs': 'EQ', 'ClsPric': 2450.50},
    {'TckrSymb': 'TCS', 'SctySrs': 'EQ', 'ClsPric': 3567.20},
    {'TckrSymb': 'SGBJAN30', 'SctySrs': 'SG', 'ClsPric': 6100.00},
    {'TckrSymb': 'SOMEBE', 'SctySrs': 'BE', 'ClsPric': 123.45},
    {'TckrSymb': 'NOCLOSE', 'SctySrs': 'EQ', 'ClsPric': None},
    {'TckrSymb': '', 'SctySrs': 'EQ', 'ClsPric': 10.0},
]


class GetStartDateTests(unittest.TestCase):
    def test_before_cutoff_uses_previous_day(self):
        now = datetime(2026, 10, 9, 16, 30, tzinfo=bhavcopy.IST)
        self.assertEqual(bhavcopy.get_start_date(now), date(2026, 10, 8))

    def test_after_cutoff_uses_today(self):
        now = datetime(2026, 10, 9, 17, 30, tzinfo=bhavcopy.IST)
        self.assertEqual(bhavcopy.get_start_date(now), date(2026, 10, 9))


class FindLatestBhavcopyTests(unittest.TestCase):
    def test_skips_weekend_and_returns_available_day(self):
        # 2026-10-11 is a Sunday; expect it to fall back to Friday 2026-10-09.
        payload = make_zip(SAMPLE_ROWS)
        calls = []

        def downloader(day):
            calls.append(day)
            return payload if day == date(2026, 10, 9) else None

        trading_date, data = bhavcopy.find_latest_bhavcopy(
            max_days=5, start_date=date(2026, 10, 11), downloader=downloader
        )

        self.assertEqual(trading_date, date(2026, 10, 9))
        self.assertEqual(data, payload)
        # Saturday/Sunday must not be requested at all.
        self.assertNotIn(date(2026, 10, 11), calls)
        self.assertNotIn(date(2026, 10, 10), calls)

    def test_raises_when_nothing_found(self):
        with self.assertRaises(RuntimeError):
            bhavcopy.find_latest_bhavcopy(
                max_days=3,
                start_date=date(2026, 10, 9),
                downloader=lambda day: None,
            )


class ExtractPricesTests(unittest.TestCase):
    def test_parses_and_filters_equity_series(self):
        prices = bhavcopy.extract_prices(make_zip(SAMPLE_ROWS), date(2026, 10, 9))
        symbols = [row['symbol'] for row in prices]

        self.assertEqual(symbols, ['RELIANCE', 'TCS', 'SOMEBE'])
        self.assertNotIn('SGBJAN30', symbols)   # non-equity series dropped
        self.assertNotIn('NOCLOSE', symbols)    # missing close dropped
        self.assertNotIn('', symbols)           # blank symbol dropped
        self.assertEqual(prices[0], {'symbol': 'RELIANCE', 'price': 2450.50})

    def test_can_disable_series_filter(self):
        prices = bhavcopy.extract_prices(
            make_zip(SAMPLE_ROWS), date(2026, 10, 9), equity_series=None
        )
        symbols = [row['symbol'] for row in prices]
        self.assertIn('SGBJAN30', symbols)

    def test_works_without_series_column(self):
        rows = [{'TckrSymb': 'INFY', 'ClsPric': 1543.75}]
        prices = bhavcopy.extract_prices(make_zip(rows), date(2026, 10, 9))
        self.assertEqual(prices, [{'symbol': 'INFY', 'price': 1543.75}])

    def test_raises_when_columns_missing(self):
        payload = make_zip([{'FOO': 'bar'}])
        with self.assertRaises(RuntimeError):
            bhavcopy.extract_prices(payload, date(2026, 10, 9))

    def test_raises_when_zip_has_no_csv(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('readme.txt', 'no csv here')
        with self.assertRaises(RuntimeError):
            bhavcopy.extract_prices(buffer.getvalue(), date(2026, 10, 9))


class DownloadBhavcopyTests(unittest.TestCase):
    class _Response:
        status_code = 200

        def iter_content(self, chunk_size=8192):
            yield b'PK\x03\x04fake-zip'

    def test_rejects_non_zip_payload(self):
        class BadResponse:
            status_code = 200

            def iter_content(self, chunk_size=8192):
                yield b'<html>error</html>'

        class FakeSession:
            def get(self, *args, **kwargs):
                return BadResponse()

        self.assertIsNone(
            bhavcopy.download_bhavcopy(date(2026, 10, 9), session=FakeSession())
        )

    def test_returns_zip_bytes_on_success(self):
        class FakeSession:
            def get(self, *args, **kwargs):
                return DownloadBhavcopyTests._Response()

        data = bhavcopy.download_bhavcopy(date(2026, 10, 9), session=FakeSession())
        self.assertEqual(data, b'PK\x03\x04fake-zip')

    def test_returns_none_on_http_error(self):
        class FakeSession:
            def get(self, *args, **kwargs):
                class Response:
                    status_code = 404

                    def iter_content(self, chunk_size=8192):
                        return iter(())

                return Response()

        self.assertIsNone(
            bhavcopy.download_bhavcopy(date(2026, 10, 9), session=FakeSession())
        )


if __name__ == '__main__':
    unittest.main()
