#!/usr/bin/env bash
set -e

echo ">>> Running database migrations..."
python -c "
import sys
try:
    from database import engine, Base
    import models
    Base.metadata.create_all(bind=engine)
    print('Tables created/verified.')
except Exception as e:
    print(f'Migration failed: {e}', file=sys.stderr)
    sys.exit(1)
"

echo ">>> Starting API..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
