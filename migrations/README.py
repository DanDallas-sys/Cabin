"""
Run this once to set up Alembic database migrations.

Usage:
    pip install -r requirements.txt
    alembic init migrations
    # Then replace migrations/env.py target_metadata with:
    #   from models import Base
    #   target_metadata = Base.metadata
    alembic revision --autogenerate -m "initial schema"
    alembic upgrade head
"""
