#!/usr/bin/env bash
# start.sh — runs on every deploy before the API starts
# Render will call this instead of uvicorn directly if you point startCommand to it

set -e  # exit immediately if any command fails

echo ">>> Running database migrations..."
python -c "
from database import engine, Base
import models  # ensures all models are registered
Base.metadata.create_all(bind=engine)
print('Tables created/verified.')
"

echo ">>> Starting API..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
