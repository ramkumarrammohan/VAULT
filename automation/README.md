# Vault Automation Service

Downloads market data from external sources and syncs it into the Vault backend
through its REST API. The first job is the **NSE bhavcopy price sync**: the
previous trading day's end-of-day close prices for your tracked INR stocks.

Design goals:

- **Backend-only integration** — the service never talks to the browser; the
  backend proxies UI-triggered jobs to it, so it needs no public port.
- **Pluggable jobs** — new automations (corporate actions, MF NAV, ...)
  subclass `automation.jobs.base.Job` and register in `automation/jobs/__init__.py`.
- **USD-safe** — bhavcopy prices only ever update INR stocks; the backend's
  `/api/prices/bulk` endpoint enforces this independently.

## How it works

```
NSE bhavcopy ──► automation/nse/bhavcopy.py ──► matched prices ──► POST /api/prices/bulk ──► MySQL
                     (download + parse)               │
                                                      └─► filter: only symbols Vault tracks
```

1. `GET /api/stocks/` → the current watchlist.
2. `find_latest_bhavcopy()` walks back up to `MAX_LOOKBACK_DAYS` weekdays from
   the 5 PM IST cutoff (handles weekends, NSE holidays, delayed uploads).
3. `extract_prices()` parses `TckrSymb` / `ClsPric`, optionally restricted to
   the equity series (`SctySrs` in `EQUITY_SERIES`, default `EQ,BE`).
4. By default (`BULK_MODE=matched`) only symbols present in the watchlist are
   sent, so the payload is your portfolio, not the whole bhavcopy. If the
   watchlist fetch fails it automatically falls back to `BULK_MODE=all`.
5. `POST /api/prices/bulk` applies only INR stocks; USD stocks are never touched.

## Stage 1 — run manually (no Docker)

Requires Python 3.11+ (uses `zoneinfo`).

```powershell
cd automation
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the HTTP service (default port **8080**):

```powershell
python -m automation.app
```

Run one job synchronously from the terminal (no server needed):

```powershell
python -m automation.cli --once
python -m automation.cli --once --date 2026-10-10
python -m automation.cli --list
```

## Job API

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET`  | `/health` | Liveness probe; also exposes the configured `backend_url`. |
| `GET`  | `/status` | Service + job-runner state (idle/running/success/error). |
| `GET`  | `/jobs` | List registered jobs. |
| `POST` | `/jobs/bhavcopy/run` | Start the bhavcopy sync (background). Body: `{"date": "YYYY-MM-DD"}`. Returns 202, or 409 if a job is running. |
| `GET`  | `/jobs/bhavcopy/status` | Job-runner state incl. `last_report` from the previous run. |

The backend proxies these as `/api/prices/sync-bhavcopy` and
`/api/prices/sync-bhavcopy/status`, so the browser never calls the automation
service directly.

## Configuration (environment variables)

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `BACKEND_URL` | `http://localhost:5000/api` | Vault backend API base URL. |
| `BACKEND_TIMEOUT` | `60` | HTTP timeout (seconds) for backend calls. |
| `AUTOMATION_HOST` / `AUTOMATION_PORT` | `0.0.0.0` / `8080` | HTTP service bind. |
| `LOG_LEVEL` | `INFO` | Logging level. |
| `MAX_LOOKBACK_DAYS` | `10` | Max calendar days to walk back for a bhavcopy. |
| `BULK_MODE` | `matched` | `matched` = send only watchlist symbols; `all` = send every row. |
| `EQUITY_SERIES` | `EQ,BE` | `SctySrs` values to keep; empty disables the filter. |
| `ARTIFACTS_DIR` | *(empty)* | When set, writes a `DATE,SYMBOL,CLOSE_PRICE` CSV per run. |

## Running the tests

From the repository root (using a Python with `pandas` installed):

```powershell
python -m unittest discover -s automation/tests -v
```

## Stage 2 — container + scheduler (planned)

- `automation/Dockerfile` runs the same `python -m automation.app` on an
  internal port (no published ports in `docker-compose.yml`).
- `automation/scheduler.py` adds APScheduler: a catch-up run shortly after
  start (`STARTUP_DELAY_SECONDS`, default 60) and a daily run at `RUN_TIME`
  (default 18:30, `TZ` default `Asia/Kolkata`) on weekdays.
- The compose service sets `BACKEND_URL=http://backend:5000/api` and
  `ENABLE_SCHEDULE=true`.

The HTTP API and job code are identical between Stage 1 and Stage 2.