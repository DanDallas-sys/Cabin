import os
import hmac
import hashlib
from fastapi import FastAPI, Depends, HTTPException, Request, Form, Header
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db, engine, Base
from schemas import TransactionIn, MonoWebhookEvent
from services.processor import process_transaction
from services.classifier import classify_with_ai
from services.report import generate_report
from services.bank_provider import parse_mono_transaction, verify_mono_signature
from models import User, ClarificationRequest, Transaction, ClarificationStatus, TransactionStatus
from config import get_settings

settings = get_settings()

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CABIN — Automated Financial Tracking API",
    version="1.0.0",
    description="Automatically tracks, categorises, and reports financial transactions.",
)

# Allow all origins for now (lock this down when you add auth)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env}


# ── Internal transaction webhook (direct / testing) ───────────────────────────

@app.post("/webhook/transaction", summary="Receive a transaction directly")
def receive_transaction(tx: TransactionIn, db: Session = Depends(get_db)):
    try:
        result = process_transaction(db, tx)
        return {"status": "processed", "transaction_id": result.id, "tx_status": result.status}
    except Exception as e:
        print(f"[Webhook] ERROR processing transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Mono webhook ──────────────────────────────────────────────────────────────

@app.post("/webhook/mono", summary="Mono bank data webhook")
async def mono_webhook(
    request: Request,
    mono_signature: str = Header(None, alias="mono-webhook-secret"),
    db: Session = Depends(get_db),
):
    body = await request.body()

    # Verify Mono signature
    if settings.mono_secret_key and mono_signature:
        if not verify_mono_signature(body, mono_signature):
            raise HTTPException(status_code=401, detail="Invalid Mono signature")

    payload = await request.json()
    event = payload.get("event", "")

    if event != "mono.events.account_updated":
        return {"status": "ignored", "event": event}

    data = payload.get("data", {})
    user_phone = data.get("meta", {}).get("phone", "")

    if not user_phone:
        raise HTTPException(status_code=400, detail="No phone number in Mono payload")

    # Mono can send multiple transactions at once
    raw_transactions = data.get("transactions", [data.get("transaction", {})])

    processed = []
    for raw_tx in raw_transactions:
        tx_data = parse_mono_transaction(raw_tx, user_phone)
        if tx_data:
            result = process_transaction(db, tx_data)
            processed.append({"id": result.id, "status": result.status})

    return {"status": "ok", "processed": processed}


# ── WhatsApp reply webhook (Twilio) ───────────────────────────────────────────

@app.post("/webhook/whatsapp", summary="Receive WhatsApp replies via Twilio")
async def whatsapp_reply(
    request: Request,
    db: Session = Depends(get_db),
):
    # Twilio sends form-encoded data
    form = await request.form()
    phone_raw = form.get("From", "")
    message = form.get("Body", "").strip()

    # Normalise: strip "whatsapp:" prefix Twilio adds
    phone = phone_raw.replace("whatsapp:", "").strip()

    if not phone or not message:
        raise HTTPException(status_code=400, detail="Missing From or Body")

    # Look up user
    user = db.query(User).filter_by(phone=phone).first()
    if not user:
        return {"status": "user_not_found"}

    # Get the most recent pending clarification for this user
    req = (
        db.query(ClarificationRequest)
        .filter_by(user_id=user.id, status=ClarificationStatus.pending)
        .order_by(ClarificationRequest.id.desc())
        .first()
    ) or (
        db.query(ClarificationRequest)
        .filter_by(user_id=user.id, status=ClarificationStatus.nudged)
        .order_by(ClarificationRequest.id.desc())
        .first()
    )

    if not req:
        return {"status": "no_pending_request"}

    # Fetch associated transaction
    tx = db.get(Transaction, req.transaction_id)
    if not tx:
        return {"status": "transaction_not_found"}

    # Try dictionary first, then AI
    from services.dictionary import match_pattern
    from services.processor import clean_narration

    cleaned_message = clean_narration(message)
    category = match_pattern(cleaned_message)

    if category:
        confidence = 1.0
    else:
        category, confidence = classify_with_ai(cleaned_message)

    tx.category = category
    tx.cleaned_narration = cleaned_message
    tx.confidence = confidence
    tx.status = TransactionStatus.processed

    req.status = ClarificationStatus.resolved
    req.resolved_at = datetime.utcnow()   # ← bug was here (was None)

    db.commit()

    return {"status": "updated", "transaction_id": tx.id, "category": category}


# ── Report download ───────────────────────────────────────────────────────────

@app.get("/report/{user_id}", summary="Download a user's transaction report as Excel")
def download_report(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_path = generate_report(db, user_id)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="Report generation failed")

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"transactions_user_{user_id}.xlsx",
    )


# ── Admin: list users ─────────────────────────────────────────────────────────

@app.get("/users", summary="List all users (admin)")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "phone": u.phone, "created_at": u.created_at} for u in users]


# ── Admin: list transactions for a user ──────────────────────────────────────

@app.get("/users/{user_id}/transactions", summary="List transactions for a user")
def list_transactions(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    txs = (
        db.query(Transaction)
        .filter_by(user_id=user_id)
        .order_by(Transaction.date.desc())
        .all()
    )

    return [
        {
            "id": tx.id,
            "amount": tx.amount,
            "category": tx.category,
            "status": tx.status,
            "type": tx.type,
            "date": tx.date,
            "narration": tx.cleaned_narration or tx.narration,
            "confidence": tx.confidence,
        }
        for tx in txs
    ]

