"""Command-line runner for automation jobs.

Examples:
    python -m automation.cli --list
    python -m automation.cli --once
    python -m automation.cli --once --date 2026-10-10
"""

import argparse
import json
import sys

from .config import config
from .jobs import available_jobs, get_job, has_job


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='python -m automation.cli',
        description='Run Vault automation jobs once (no server, no scheduler).',
    )
    parser.add_argument('--job', default='bhavcopy', help='job name (default: bhavcopy)')
    parser.add_argument('--once', action='store_true', help='run the job once and exit')
    parser.add_argument('--date', help='target trading date (YYYY-MM-DD)')
    parser.add_argument(
        '--lookback-days', type=int,
        help='override how many days to walk back looking for a bhavcopy',
    )
    parser.add_argument('--list', action='store_true', help='list available jobs and exit')
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    from .app import configure_logging

    configure_logging()

    if args.list:
        for job in available_jobs():
            print(f"{job['name']:<12} {job['description']}")
        return 0

    if not has_job(args.job):
        print(f"Unknown job '{args.job}'. Available: "
              f"{', '.join(j['name'] for j in available_jobs())}", file=sys.stderr)
        return 2

    kwargs = {}
    if args.date:
        kwargs['trading_date'] = args.date
    if args.lookback_days:
        kwargs['lookback_days'] = args.lookback_days

    print(f"Running job '{args.job}' against {config.BACKEND_URL} ...")
    report = get_job(args.job).run(**kwargs)
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
