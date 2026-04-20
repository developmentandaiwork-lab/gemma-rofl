#!/usr/bin/env sh
set -eu

echo "Waiting for Postgres at db:5432..."
until nc -z db 5432; do
  sleep 1
done

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Uvicorn..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
