#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
exec python -m fastapi run app/main.py --host 0.0.0.0 --port 8000
