"""HTTP service exposing automation jobs.

Stage 1 runs this manually, alongside the backend:

    python -m automation.app          # serves on http://localhost:8080

The backend proxies UI requests to this service, so it is never exposed to the
browser directly.
"""

import logging
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from .config import config
from .jobs import available_jobs, get_job, has_job

logger = logging.getLogger(__name__)

SERVICE_NAME = 'vault-automation'


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def configure_logging(level: str | None = None) -> None:
    logging.basicConfig(
        level=(level or config.LOG_LEVEL),
        format='%(asctime)s %(levelname)-7s %(name)s: %(message)s',
    )


class JobRunner:
    """Tracks a single running job at a time (in-process, thread-based)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._state = {
            'status': 'idle',        # idle | running | success | error
            'current_job': None,
            'started_at': None,
            'finished_at': None,
            'last_report': None,
            'error': None,
            'runs': 0,
        }

    def status(self) -> dict:
        with self._lock:
            return dict(self._state)

    def is_running(self) -> bool:
        with self._lock:
            return self._state['status'] == 'running'

    def start(self, job_name: str, **kwargs) -> bool:
        """Start a job in the background. Returns False if one is running."""
        with self._lock:
            if self._state['status'] == 'running':
                return False
            self._state.update({
                'status': 'running',
                'current_job': job_name,
                'started_at': _utcnow_iso(),
                'finished_at': None,
                'last_report': None,
                'error': None,
            })

        thread = threading.Thread(
            target=self._execute, args=(job_name,), kwargs=kwargs, daemon=True
        )
        thread.start()
        return True

    def _execute(self, job_name: str, **kwargs) -> None:
        try:
            report = get_job(job_name).run(**kwargs)
            with self._lock:
                self._state.update({
                    'status': 'success',
                    'finished_at': _utcnow_iso(),
                    'last_report': report,
                    'runs': self._state['runs'] + 1,
                })
            logger.info("job '%s' completed", job_name)
        except Exception as exc:  # noqa: BLE001 - surfaced via status endpoint
            logger.exception("job '%s' failed", job_name)
            with self._lock:
                self._state.update({
                    'status': 'error',
                    'finished_at': _utcnow_iso(),
                    'error': str(exc),
                    'runs': self._state['runs'] + 1,
                })


def create_app() -> Flask:
    configure_logging()

    app = Flask(__name__)
    runner = JobRunner()
    app.config['JOB_RUNNER'] = runner

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'ok',
            'service': SERVICE_NAME,
            'backend_url': config.BACKEND_URL,
        })

    @app.route('/status', methods=['GET'])
    def status():
        return jsonify({
            'service': SERVICE_NAME,
            'backend_url': config.BACKEND_URL,
            'jobs': available_jobs(),
            **runner.status(),
        })

    @app.route('/jobs', methods=['GET'])
    def list_jobs():
        return jsonify({'jobs': available_jobs()})

    @app.route('/jobs/<string:job_name>/run', methods=['POST'])
    def run_job(job_name: str):
        if not has_job(job_name):
            return jsonify({'error': f"Unknown job '{job_name}'"}), 404

        payload = request.get_json(silent=True) or {}
        kwargs = {}
        if payload.get('date'):
            kwargs['trading_date'] = payload['date']
        if payload.get('lookback_days'):
            try:
                kwargs['lookback_days'] = int(payload['lookback_days'])
            except (TypeError, ValueError):
                return jsonify({'error': "'lookback_days' must be an integer"}), 400

        if not runner.start(job_name, **kwargs):
            return jsonify({
                'error': 'A job is already running',
                **runner.status(),
            }), 409

        return jsonify({'status': 'started', **runner.status()}), 202

    @app.route('/jobs/<string:job_name>/status', methods=['GET'])
    def job_status(job_name: str):
        if not has_job(job_name):
            return jsonify({'error': f"Unknown job '{job_name}'"}), 404
        return jsonify({'job': job_name, **runner.status()})

    return app


app = create_app()


if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=False)
