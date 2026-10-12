"""Vault automation service.

Runs scheduled / on-demand data-sync jobs (starting with the NSE bhavcopy
price sync) and pushes results into the Vault backend via its REST API.

Stage 1 is run manually, exactly like the backend:

    python -m automation.app      # HTTP service on :8080
    python -m automation.cli --once   # single run, no server

Stage 2 wraps this package in a container and adds a scheduler.
"""

__version__ = "0.1.0"
