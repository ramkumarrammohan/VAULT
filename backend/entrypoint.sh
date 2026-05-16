#!/bin/bash
set -e

DB_HOST="${DB_HOST:-vault_db}"
DB_PORT="${DB_PORT:-3306}"

echo "Waiting for MySQL at ${DB_HOST}:${DB_PORT}..."
until python -c "
import socket, sys
try:
    s = socket.create_connection(('${DB_HOST}', ${DB_PORT}), timeout=2)
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  echo "  MySQL not ready yet, retrying in 3s..."
  sleep 3
done

echo "MySQL is ready."

echo "Running database migrations..."
flask db upgrade

echo "Starting gunicorn..."
exec gunicorn \
  --bind 0.0.0.0:5000 \
  --workers "${GUNICORN_WORKERS:-4}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  "app:create_app()"
