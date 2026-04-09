from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from models import (
    Transaction, User, ClarificationRequest,
    TransactionStatus, TransactionType, ClarificationStatus
)
from services.dictionary import match_pattern
from services.classifier import classify_with_ai
from services.whatsapp import send_clarification_prompt
from schemas import TransactionIn
from config import get_settings

settings = get_settings()


# ── Helpers ───────────────────────────────────────────────────────────────────

def clean_narration(narration: str | None) -> str:
    """Lowercase, strip whitespace, collapse multiple spaces."""
    if not narration:
        return ""
    import re
    return re.sub(r"\s+", " ", narration.lower().strip())


def _get_or_create_user(db: Session, phone: str) -> User:
    user = db.query(User).filter_by(phone=phone).first()
    if not user:
        user = User(phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _detect_reversal(db: Session, tx: Transaction) -> bool:
    """
    Look for a recent transaction with the exact opposite amount
    within the last 3 days. If found, mark both as reversals.
    """
    opposite = db.query(Transaction).filter(
        Transaction.amount == -tx.amount,
        Transaction.user_id == tx.user_id,
        Transaction.created_at >= datetime.utcnow() - timedelta(days=3),
        Transaction.status != TransactionStatus.reversal,
    ).first()

    if opposite:
        opposite.type = TransactionType.reversal
        opposite.status = TransactionStatus.reversal
        opposite.category = "reversal"
        tx.type = TransactionType.reversal
        tx.status = TransactionStatus.reversal
        tx.category = "reversal"
        return True

    return False


# ── Main processor ────────────────────────────────────────────────────────────

def process_transaction(db: Session, tx_data: TransactionIn) -> Transaction:
    # 1. Get or create user
    user = _get_or_create_user(db, tx_data.user_phone)

    # 2. Deduplication — skip if reference already exists
    existing = db.query(Transaction).filter_by(reference=tx_data.reference).first()
    if existing:
        return existing

    # 3. Clean narration
    cleaned = clean_narration(tx_data.narration)

    # 4. Determine base type from amount
    base_type = TransactionType.credit if tx_data.amount > 0 else TransactionType.debit

    tx = Transaction(
        user_id=user.id,
        amount=tx_data.amount,
        narration=tx_data.narration,
        cleaned_narration=cleaned or None,
        reference=tx_data.reference,
        type=base_type,
        date=tx_data.date,
        created_at=datetime.utcnow(),
        status=TransactionStatus.pending,
    )

    # 5. Reversal detection (needs DB flush to query against)
    if _detect_reversal(db, tx):
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx

    # 6. No narration → send WhatsApp, create clarification request
    if not cleaned:
        try:
            tx.status = TransactionStatus.pending
            db.add(tx)
            db.commit()
            db.refresh(tx)
        except Exception as e:
            db.rollback()
            print(f"[Processor] ERROR saving transaction: {e}")
            raise

        send_clarification_prompt(user.phone, tx.amount, tx.type.value)

        try:
            req = ClarificationRequest(
                transaction_id=tx.id,
                user_id=user.id,
                status=ClarificationStatus.pending,
                prompt_sent_at=datetime.utcnow(),
            )
            db.add(req)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[Processor] ERROR saving clarification request: {e}")
            raise
        return tx

    # 7. Pattern match (free, instant)
    category = match_pattern(cleaned)
    if category:
        tx.category = category
        tx.confidence = 1.0
        tx.status = TransactionStatus.processed
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx

    # 8. AI classification
    category, confidence = classify_with_ai(cleaned)
    tx.category = category
    tx.confidence = confidence

    if confidence >= settings.ai_confidence_threshold:
        tx.status = TransactionStatus.processed
    else:
        tx.status = TransactionStatus.low_confidence

    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx
