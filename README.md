# CABIN — Automated Financial Tracking System

A production-ready backend that automatically tracks, categorises, and reports financial transactions using AI, WhatsApp, and Nigerian bank APIs.

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Database | PostgreSQL + SQLAlchemy 2.0 |
| AI Classifier | Anthropic Claude (Haiku) |
| WhatsApp | Twilio |
| Background Jobs | Celery + Redis |
| Bank Data | Mono / Okra / Stitch |
| Reports | Pandas + OpenPyXL |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your real credentials
```

Required values:
- `DATABASE_URL` — your PostgreSQL connection string
- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` — from twilio.com/console
- `TWILIO_WHATSAPP_FROM` — your approved WhatsApp sender number
- `MONO_SECRET_KEY` — from your Mono dashboard

### 3. Set up the database

```bash
# Option A: Let FastAPI auto-create tables (dev only)
# Tables are created automatically on first startup.

# Option B: Use Alembic (recommended for production)
alembic init migrations
# Edit migrations/env.py → set target_metadata = Base.metadata
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### 4. Start the API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Start the Celery worker + beat scheduler

```bash
# Worker (processes tasks)
celery -A celery_worker worker --loglevel=info

# Beat scheduler (triggers daily job)
celery -A celery_worker beat --loglevel=info
```

---

## API Endpoints

### Webhooks

| Method | Path | Description |
|---|---|---|
| POST | `/webhook/transaction` | Submit a transaction directly (for testing) |
| POST | `/webhook/mono` | Mono bank data webhook |
| POST | `/webhook/whatsapp` | Twilio WhatsApp reply webhook |

### Reports & Data

| Method | Path | Description |
|---|---|---|
| GET | `/report/{user_id}` | Download Excel transaction report |
| GET | `/users` | List all users |
| GET | `/users/{user_id}/transactions` | List transactions for a user |
| GET | `/health` | Health check |

---

## Transaction Lifecycle

```
Incoming Transaction
        │
        ├─► Duplicate? → Skip
        │
        ├─► Reversal detected? → Mark both as reversal
        │
        ├─► No narration? → WhatsApp user, create clarification request
        │                        │
        │                   Day 2: Nudge
        │                   Day 4: Mark uncategorized
        │
        ├─► Pattern match? → processed (confidence = 1.0)
        │
        └─► AI classify
              ├─► confidence ≥ 0.75 → processed
              └─► confidence < 0.75 → low_confidence
```

---

## WhatsApp Flow

1. Transaction arrives with no narration
2. User receives: *"₦5,000.00 was debited from your account. What was this for?"*
3. User replies: *"Uber ride to the island"*
4. AI classifies reply → `transport` category
5. Transaction updated to `processed`

---

## Adding Bank Providers

See `services/bank_provider.py`. To add a new provider:

1. Write a `parse_PROVIDER_transaction(event_data, user_phone)` function
2. Add it to the `parsers` dict in `parse_bank_transaction()`
3. Add a new webhook route in `main.py`

---

## Adding Transaction Categories

Edit `services/dictionary.py` — add keywords to `KNOWN_PATTERNS`.
The AI classifier handles everything not in the dictionary automatically.

---

## Deployment (Production)

```bash
# With gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# With Docker (add your own Dockerfile)
# Ensure REDIS and POSTGRES are reachable from the container
```

### Twilio WhatsApp webhook URL
Point this in your Twilio console to:
```
https://yourdomain.com/webhook/whatsapp
```

### Mono webhook URL
Point this in your Mono dashboard to:
```
https://yourdomain.com/webhook/mono
```
